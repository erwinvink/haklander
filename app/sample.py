"""Create a sample DXF file for testing."""
import ezdxf

# Create a new DXF document
doc = ezdxf.new('R2010')
msp = doc.modelspace()

# Add some layers
doc.layers.add('WALLS', color=7)  # White
doc.layers.add('DOORS', color=4)  # Cyan
doc.layers.add('DIMENSIONS', color=6)  # Magenta
doc.layers.add('TEXT', color=3)  # Green

# Draw floor plan outline
msp.add_lwpolyline(
    [(0, 0), (10000, 0), (10000, 8000), (0, 8000), (0, 0)],
    dxfattribs={'layer': 'WALLS'}
)

# Interior walls
msp.add_line((4000, 0), (4000, 4000), dxfattribs={'layer': 'WALLS'})
msp.add_line((4000, 4000), (6000, 4000), dxfattribs={'layer': 'WALLS'})
msp.add_line((6000, 4000), (6000, 8000), dxfattribs={'layer': 'WALLS'})

# Doors (represented as arcs)
msp.add_arc((4000, 2500), 800, 0, 90, dxfattribs={'layer': 'DOORS'})
msp.add_arc((7500, 4000), 800, 90, 180, dxfattribs={'layer': 'DOORS'})

# Room labels
msp.add_text('LIVING ROOM', dxfattribs={'layer': 'TEXT', 'height': 300}).set_placement((2000, 6000))
msp.add_text('KITCHEN', dxfattribs={'layer': 'TEXT', 'height': 300}).set_placement((2000, 2000))
msp.add_text('BEDROOM', dxfattribs={'layer': 'TEXT', 'height': 300}).set_placement((7500, 6000))
msp.add_text('BATHROOM', dxfattribs={'layer': 'TEXT', 'height': 300}).set_placement((7500, 2000))

# Dimension lines (simplified)
msp.add_line((0, -500), (10000, -500), dxfattribs={'layer': 'DIMENSIONS'})
msp.add_line((0, -300), (0, -700), dxfattribs={'layer': 'DIMENSIONS'})
msp.add_line((10000, -300), (10000, -700), dxfattribs={'layer': 'DIMENSIONS'})
msp.add_text('10000', dxfattribs={'layer': 'DIMENSIONS', 'height': 200}).set_placement((5000, -800))

msp.add_line((-500, 0), (-500, 8000), dxfattribs={'layer': 'DIMENSIONS'})
msp.add_line((-300, 0), (-700, 0), dxfattribs={'layer': 'DIMENSIONS'})
msp.add_line((-300, 8000), (-700, 8000), dxfattribs={'layer': 'DIMENSIONS'})
msp.add_text('8000', dxfattribs={'layer': 'DIMENSIONS', 'height': 200}).set_placement((-1200, 4000))

# Save the file
doc.saveas('sample_floorplan.dxf')
print('Created sample_floorplan.dxf')
