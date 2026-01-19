"""
DXF Chat Editor - A simple DXF editor with AI chat interface.

Upload DXF -> Backend converts to SVG -> User chats -> AI generates ezdxf code -> Execute -> Update SVG
"""

import io
import os
import tempfile
import traceback
from pathlib import Path
from typing import Optional

import anthropic
import ezdxf
from ezdxf.addons.drawing import Frontend, RenderContext
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="DXF Chat Editor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store the current DXF document in memory (simple approach for single user)
current_doc: Optional[ezdxf.document.Drawing] = None
current_filename: str = ""
temp_dir = tempfile.mkdtemp()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    code: str
    executed: bool
    result: str
    svg_updated: bool


def dxf_to_svg(doc: ezdxf.document.Drawing) -> str:
    """Convert ezdxf document to SVG string using ezdxf's SVG backend."""
    from ezdxf.addons.drawing import svg, layout
    from ezdxf.addons.drawing.config import Configuration, ColorPolicy, BackgroundPolicy

    # Configure for light background with black lines
    config = Configuration(
        background_policy=BackgroundPolicy.OFF,  # Transparent (we'll add bg in CSS)
        color_policy=ColorPolicy.BLACK,  # All lines black
        lineweight_scaling=1.5,  # Slightly thicker lines
    )

    # Use ezdxf's SVG backend for better compatibility
    backend = svg.SVGBackend()
    ctx = RenderContext(doc)
    Frontend(ctx, backend, config=config).draw_layout(doc.modelspace())

    # Auto-size page (0, 0 means auto)
    page = layout.Page(0, 0)

    svg_string = backend.get_string(page)

    return svg_string


def get_layers_info(doc: ezdxf.document.Drawing) -> list[dict]:
    """Get information about layers in the document."""
    layers = []
    for layer in doc.layers:
        entity_count = len(list(doc.modelspace().query(f'*[layer=="{layer.dxf.name}"]')))
        layers.append({
            "name": layer.dxf.name,
            "color": layer.color,
            "entity_count": entity_count
        })
    return layers


def generate_ezdxf_code(user_message: str, layers_info: list[dict]) -> tuple[str, str]:
    """Use Claude to generate ezdxf code from natural language."""
    client = anthropic.Anthropic()

    layers_desc = "\n".join([f"- {l['name']}: {l['entity_count']} entities" for l in layers_info])

    system_prompt = f"""You are an expert at writing ezdxf Python code to modify DXF files.

The current DXF document has these layers:
{layers_desc}

The user will describe changes they want to make. Generate Python code that:
1. Uses the variable `doc` which is already loaded as an ezdxf document
2. Uses `msp = doc.modelspace()` to access entities
3. Makes the requested modifications
4. Does NOT save the file (that's handled separately)

Common ezdxf patterns:
- Query entities: `msp.query('*[layer=="LAYERNAME"]')` or `msp.query('LINE')`, `msp.query('TEXT')`
- Delete entity: `msp.delete_entity(entity)`
- Change text: `entity.dxf.text = "new text"` for TEXT entities
- Change layer: `entity.dxf.layer = "NEW_LAYER"`
- Add line: `msp.add_line((x1,y1), (x2,y2), dxfattribs={{"layer": "LAYER"}})`
- Add text: `msp.add_text("text", dxfattribs={{"layer": "LAYER", "height": 2.5}}).set_placement((x, y))`

Respond with:
1. A brief explanation of what you'll do (1-2 sentences)
2. The Python code block

Format your response as:
EXPLANATION: <your explanation>
CODE:
```python
<your code>
```"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}]
    )

    text = response.content[0].text

    # Parse explanation and code
    explanation = ""
    code = ""

    if "EXPLANATION:" in text:
        parts = text.split("CODE:")
        explanation = parts[0].replace("EXPLANATION:", "").strip()
        if len(parts) > 1:
            code_part = parts[1]
            # Extract code from markdown code block
            if "```python" in code_part:
                code = code_part.split("```python")[1].split("```")[0].strip()
            elif "```" in code_part:
                code = code_part.split("```")[1].split("```")[0].strip()
            else:
                code = code_part.strip()
    else:
        explanation = "Executing requested changes."
        if "```python" in text:
            code = text.split("```python")[1].split("```")[0].strip()
        elif "```" in text:
            code = text.split("```")[1].split("```")[0].strip()

    return explanation, code


def execute_ezdxf_code(code: str, doc: ezdxf.document.Drawing) -> str:
    """Execute ezdxf code safely and return result message."""
    # Create execution environment
    exec_globals = {
        "doc": doc,
        "ezdxf": ezdxf,
    }
    exec_locals = {}

    # Count entities before
    msp = doc.modelspace()
    count_before = len(list(msp))

    try:
        exec(code, exec_globals, exec_locals)

        # Count entities after
        count_after = len(list(msp))
        diff = count_after - count_before

        if diff < 0:
            return f"{abs(diff)} element(s) removed"
        elif diff > 0:
            return f"{diff} element(s) added"
        else:
            return "Changes applied successfully"

    except Exception as e:
        raise RuntimeError(f"Code execution failed: {str(e)}\n{traceback.format_exc()}")


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the frontend HTML."""
    html_path = Path(__file__).parent / "static" / "index.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text())
    return HTMLResponse(content="<h1>Frontend not found</h1>", status_code=404)


@app.post("/api/upload")
async def upload_dxf(file: UploadFile = File(...)):
    """Upload a DXF file and convert to SVG."""
    global current_doc, current_filename

    if not file.filename.lower().endswith('.dxf'):
        raise HTTPException(status_code=400, detail="File must be a DXF file")

    # Read file content
    content = await file.read()

    # Save to temp file (ezdxf needs file path)
    temp_path = Path(temp_dir) / file.filename
    temp_path.write_bytes(content)

    try:
        # Load DXF
        current_doc = ezdxf.readfile(str(temp_path))
        current_filename = file.filename

        # Convert to SVG
        svg_content = dxf_to_svg(current_doc)

        # Get layers info
        layers = get_layers_info(current_doc)

        return {
            "success": True,
            "filename": file.filename,
            "svg": svg_content,
            "layers": layers
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process DXF: {str(e)}")


@app.get("/api/svg")
async def get_svg():
    """Get current SVG representation."""
    global current_doc

    if current_doc is None:
        raise HTTPException(status_code=404, detail="No DXF file loaded")

    svg_content = dxf_to_svg(current_doc)
    return Response(content=svg_content, media_type="image/svg+xml")


@app.get("/api/layers")
async def get_layers():
    """Get layers information."""
    global current_doc

    if current_doc is None:
        raise HTTPException(status_code=404, detail="No DXF file loaded")

    return {"layers": get_layers_info(current_doc)}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process chat message and execute ezdxf code."""
    global current_doc

    if current_doc is None:
        raise HTTPException(status_code=400, detail="No DXF file loaded. Please upload a file first.")

    try:
        # Get layers info for context
        layers = get_layers_info(current_doc)

        # Generate code using Claude
        explanation, code = generate_ezdxf_code(request.message, layers)

        if not code:
            return ChatResponse(
                response=explanation or "I couldn't generate code for that request. Please try rephrasing.",
                code="",
                executed=False,
                result="",
                svg_updated=False
            )

        # Execute the code
        result = execute_ezdxf_code(code, current_doc)

        return ChatResponse(
            response=explanation,
            code=code,
            executed=True,
            result=result,
            svg_updated=True
        )

    except RuntimeError as e:
        return ChatResponse(
            response=f"Error executing code: {str(e)}",
            code=code if 'code' in dir() else "",
            executed=False,
            result=str(e),
            svg_updated=False
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")


@app.get("/api/export/dxf")
async def export_dxf():
    """Export current DXF file."""
    global current_doc, current_filename

    if current_doc is None:
        raise HTTPException(status_code=404, detail="No DXF file loaded")

    # Save to temp file
    export_name = current_filename.replace('.dxf', '_edited.dxf')
    export_path = Path(temp_dir) / export_name
    current_doc.saveas(str(export_path))

    return FileResponse(
        path=str(export_path),
        filename=export_name,
        media_type="application/dxf"
    )


@app.get("/api/export/pdf")
async def export_pdf():
    """Export current drawing as PDF."""
    global current_doc, current_filename

    if current_doc is None:
        raise HTTPException(status_code=404, detail="No DXF file loaded")

    from ezdxf.addons.drawing import svg, layout
    from ezdxf.addons.drawing.config import Configuration, ColorPolicy, BackgroundPolicy

    # Configure for PDF export (white background, normal colors)
    config = Configuration(
        background_policy=BackgroundPolicy.WHITE,
        color_policy=ColorPolicy.COLOR,
        lineweight_scaling=2.0,
    )

    # First create SVG
    backend = svg.SVGBackend()
    ctx = RenderContext(current_doc)
    Frontend(ctx, backend, config=config).draw_layout(current_doc.modelspace())
    svg_string = backend.get_string(layout.Page(0, 0))

    # Save SVG temporarily
    svg_path = Path(temp_dir) / "temp.svg"
    svg_path.write_text(svg_string)

    # Convert SVG to PDF using svglib/reportlab
    from svglib.svglib import svg2rlg
    from reportlab.graphics import renderPDF

    drawing = svg2rlg(str(svg_path))
    if drawing is None:
        raise HTTPException(status_code=500, detail="Failed to parse SVG for PDF export")

    export_name = current_filename.replace('.dxf', '.pdf')
    export_path = Path(temp_dir) / export_name
    renderPDF.drawToFile(drawing, str(export_path))

    return FileResponse(
        path=str(export_path),
        filename=export_name,
        media_type="application/pdf"
    )


def run():
    """Run the server."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    run()
