/**
 * HAKLANDER INTERIEURBOUW - Main JavaScript
 * Award-Winning Website Interactions
 */

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', () => {
  initLoader();
  initNavigation();
  initCustomCursor();
  initScrollReveal();
  initSmoothScroll();
  initParallax();
  initCounterAnimation();
  initMobileMenu();
  initFormValidation();
});

/**
 * Loading Screen
 */
function initLoader() {
  const loader = document.querySelector('.loader');
  if (!loader) return;

  window.addEventListener('load', () => {
    setTimeout(() => {
      loader.classList.add('hidden');
      document.body.style.overflow = '';
    }, 1800);
  });

  // Prevent scroll during loading
  document.body.style.overflow = 'hidden';
}

/**
 * Navigation Scroll Effect
 */
function initNavigation() {
  const nav = document.querySelector('.nav');
  if (!nav) return;

  let lastScroll = 0;

  window.addEventListener('scroll', () => {
    const currentScroll = window.pageYOffset;

    // Add scrolled class when past threshold
    if (currentScroll > 100) {
      nav.classList.add('scrolled');
    } else {
      nav.classList.remove('scrolled');
    }

    // Hide/show nav on scroll direction
    if (currentScroll > lastScroll && currentScroll > 500) {
      nav.style.transform = 'translateY(-100%)';
    } else {
      nav.style.transform = 'translateY(0)';
    }

    lastScroll = currentScroll;
  });

  // Set active nav link based on current page
  const currentPage = window.location.pathname.split('/').pop() || 'index.html';
  const navLinks = document.querySelectorAll('.nav__link');

  navLinks.forEach(link => {
    const href = link.getAttribute('href');
    if (href === currentPage || (currentPage === '' && href === 'index.html')) {
      link.classList.add('active');
    }
  });
}

/**
 * Custom Cursor
 */
function initCustomCursor() {
  // Only init on devices with mouse
  if (window.matchMedia('(hover: none)').matches) return;

  const cursor = document.createElement('div');
  cursor.className = 'cursor';
  document.body.appendChild(cursor);

  const cursorDot = document.createElement('div');
  cursorDot.className = 'cursor-dot';
  document.body.appendChild(cursorDot);

  let mouseX = 0;
  let mouseY = 0;
  let cursorX = 0;
  let cursorY = 0;

  document.addEventListener('mousemove', (e) => {
    mouseX = e.clientX;
    mouseY = e.clientY;
    cursorDot.style.left = mouseX + 'px';
    cursorDot.style.top = mouseY + 'px';
  });

  // Smooth cursor follow
  function animateCursor() {
    const dx = mouseX - cursorX;
    const dy = mouseY - cursorY;

    cursorX += dx * 0.15;
    cursorY += dy * 0.15;

    cursor.style.left = cursorX + 'px';
    cursor.style.top = cursorY + 'px';

    requestAnimationFrame(animateCursor);
  }
  animateCursor();

  // Cursor hover effects
  const hoverElements = document.querySelectorAll('a, button, .project-card, .expertise-card');

  hoverElements.forEach(el => {
    el.addEventListener('mouseenter', () => {
      cursor.classList.add('hover');
    });
    el.addEventListener('mouseleave', () => {
      cursor.classList.remove('hover');
    });
  });

  // Hide cursor when leaving window
  document.addEventListener('mouseleave', () => {
    cursor.style.opacity = '0';
    cursorDot.style.opacity = '0';
  });

  document.addEventListener('mouseenter', () => {
    cursor.style.opacity = '1';
    cursorDot.style.opacity = '1';
  });
}

/**
 * Scroll Reveal Animations
 */
function initScrollReveal() {
  const revealElements = document.querySelectorAll('.reveal, .reveal-left, .reveal-right, .reveal-scale');

  const observerOptions = {
    root: null,
    rootMargin: '0px',
    threshold: 0.1
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('active');
        // Optionally unobserve after animation
        // observer.unobserve(entry.target);
      }
    });
  }, observerOptions);

  revealElements.forEach(el => {
    observer.observe(el);
  });
}

/**
 * Smooth Scroll for anchor links
 */
function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      e.preventDefault();
      const target = document.querySelector(this.getAttribute('href'));

      if (target) {
        const headerOffset = 100;
        const elementPosition = target.getBoundingClientRect().top;
        const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

        window.scrollTo({
          top: offsetPosition,
          behavior: 'smooth'
        });
      }
    });
  });
}

/**
 * Parallax Effects
 */
function initParallax() {
  const parallaxElements = document.querySelectorAll('[data-parallax]');

  if (parallaxElements.length === 0) return;

  window.addEventListener('scroll', () => {
    const scrolled = window.pageYOffset;

    parallaxElements.forEach(el => {
      const speed = el.dataset.parallax || 0.5;
      const yPos = -(scrolled * speed);
      el.style.transform = `translateY(${yPos}px)`;
    });
  });
}

/**
 * Counter Animation for Stats
 */
function initCounterAnimation() {
  const counters = document.querySelectorAll('.stat__number');

  if (counters.length === 0) return;

  const observerOptions = {
    threshold: 0.5
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const counter = entry.target;
        const target = parseInt(counter.dataset.count);
        const suffix = counter.dataset.suffix || '';
        const duration = 2000;
        const start = 0;
        const startTime = performance.now();

        function updateCounter(currentTime) {
          const elapsed = currentTime - startTime;
          const progress = Math.min(elapsed / duration, 1);

          // Easing function (ease-out)
          const easeOut = 1 - Math.pow(1 - progress, 3);
          const current = Math.floor(start + (target - start) * easeOut);

          counter.textContent = current + suffix;

          if (progress < 1) {
            requestAnimationFrame(updateCounter);
          }
        }

        requestAnimationFrame(updateCounter);
        observer.unobserve(counter);
      }
    });
  }, observerOptions);

  counters.forEach(counter => {
    observer.observe(counter);
  });
}

/**
 * Mobile Menu Toggle
 */
function initMobileMenu() {
  const toggle = document.querySelector('.nav__toggle');
  const menu = document.querySelector('.nav__menu');

  if (!toggle || !menu) return;

  toggle.addEventListener('click', () => {
    toggle.classList.toggle('active');
    menu.classList.toggle('active');
    document.body.classList.toggle('menu-open');
  });

  // Close menu when clicking a link
  const menuLinks = menu.querySelectorAll('.nav__link');
  menuLinks.forEach(link => {
    link.addEventListener('click', () => {
      toggle.classList.remove('active');
      menu.classList.remove('active');
      document.body.classList.remove('menu-open');
    });
  });

  // Close menu on escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && menu.classList.contains('active')) {
      toggle.classList.remove('active');
      menu.classList.remove('active');
      document.body.classList.remove('menu-open');
    }
  });
}

/**
 * Form Validation
 */
function initFormValidation() {
  const form = document.querySelector('.contact-form');

  if (!form) return;

  form.addEventListener('submit', (e) => {
    e.preventDefault();

    const formData = new FormData(form);
    const data = Object.fromEntries(formData);

    // Simple validation
    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');

    requiredFields.forEach(field => {
      if (!field.value.trim()) {
        isValid = false;
        field.style.borderColor = '#e74c3c';
      } else {
        field.style.borderColor = '';
      }
    });

    // Email validation
    const emailField = form.querySelector('input[type="email"]');
    if (emailField && emailField.value) {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(emailField.value)) {
        isValid = false;
        emailField.style.borderColor = '#e74c3c';
      }
    }

    if (isValid) {
      // Simulate form submission
      const submitBtn = form.querySelector('.form__submit');
      const originalText = submitBtn.textContent;
      submitBtn.textContent = 'Verzonden!';
      submitBtn.style.background = '#27ae60';

      setTimeout(() => {
        form.reset();
        submitBtn.textContent = originalText;
        submitBtn.style.background = '';
      }, 3000);
    }
  });

  // Remove error styling on input
  const inputs = form.querySelectorAll('.form__input, .form__textarea');
  inputs.forEach(input => {
    input.addEventListener('input', () => {
      input.style.borderColor = '';
    });
  });
}

/**
 * Magnetic Button Effect
 */
function initMagneticButtons() {
  const buttons = document.querySelectorAll('.btn--magnetic');

  buttons.forEach(button => {
    button.addEventListener('mousemove', (e) => {
      const rect = button.getBoundingClientRect();
      const x = e.clientX - rect.left - rect.width / 2;
      const y = e.clientY - rect.top - rect.height / 2;

      button.style.transform = `translate(${x * 0.3}px, ${y * 0.3}px)`;
    });

    button.addEventListener('mouseleave', () => {
      button.style.transform = 'translate(0, 0)';
    });
  });
}

/**
 * Image Lazy Loading
 */
function initLazyLoading() {
  const lazyImages = document.querySelectorAll('img[data-src]');

  const imageObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const img = entry.target;
        img.src = img.dataset.src;
        img.removeAttribute('data-src');
        imageObserver.unobserve(img);
      }
    });
  });

  lazyImages.forEach(img => {
    imageObserver.observe(img);
  });
}

/**
 * Text Split Animation Helper
 */
function splitText(element) {
  const text = element.textContent;
  element.innerHTML = '';

  text.split('').forEach((char, i) => {
    const span = document.createElement('span');
    span.textContent = char === ' ' ? '\u00A0' : char;
    span.style.animationDelay = `${i * 0.03}s`;
    element.appendChild(span);
  });
}

/**
 * Throttle Function Helper
 */
function throttle(func, limit) {
  let inThrottle;
  return function(...args) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
}

/**
 * Debounce Function Helper
 */
function debounce(func, wait) {
  let timeout;
  return function(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}
