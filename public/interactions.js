/**
 * TranslateHub — Custom UI Interactions
 * Premium animations and enhanced UX
 */

// ============================================
// SUGGESTION CARD CLICK HANDLER
// ============================================
function sendSuggestion(language) {
  // Find the input field and set its value
  const input = document.querySelector('textarea') || 
                document.querySelector('#chat-input') || 
                document.querySelector('input[type="text"]');
  
  if (input) {
    // Set the value
    const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
      window.HTMLTextAreaElement.prototype, 'value'
    )?.set || Object.getOwnPropertyDescriptor(
      window.HTMLInputElement.prototype, 'value'
    )?.set;
    
    if (nativeInputValueSetter) {
      nativeInputValueSetter.call(input, language);
    } else {
      input.value = language;
    }
    
    // Trigger input events
    input.dispatchEvent(new Event('input', { bubbles: true }));
    input.dispatchEvent(new Event('change', { bubbles: true }));
    
    // Focus the input
    input.focus();
    
    // Try to find and click the send button after a short delay
    setTimeout(() => {
      const sendBtn = document.querySelector('button[class*="send"]') ||
                      document.querySelector('button[type="submit"]');
      if (sendBtn) {
        sendBtn.click();
      }
    }, 100);
  }
}

// ============================================
// SMOOTH SCROLL TO BOTTOM
// ============================================
function scrollToBottom() {
  const chatContainer = document.querySelector('[class*="messages"]') ||
                        document.querySelector('[class*="chat-content"]') ||
                        document.querySelector('[class*="chat-container"]');
  if (chatContainer) {
    chatContainer.scrollTo({
      top: chatContainer.scrollHeight,
      behavior: 'smooth'
    });
  }
}

// ============================================
// MESSAGE ENTRANCE ANIMATION
// ============================================
const observerOptions = {
  root: null,
  rootMargin: '0px',
  threshold: 0.1
};

const messageObserver = new MutationObserver((mutations) => {
  mutations.forEach((mutation) => {
    if (mutation.type === 'childList') {
      mutation.addedNodes.forEach((node) => {
        if (node.nodeType === 1) {
          // Check if it's a message element
          if (node.classList?.contains('message') || 
              node.getAttribute?.('class')?.includes('message')) {
            node.style.opacity = '0';
            node.style.transform = 'translateY(12px)';
            requestAnimationFrame(() => {
              node.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
              node.style.opacity = '1';
              node.style.transform = 'translateY(0)';
            });
          }
        }
      });
    }
  });
});

// Start observing when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  const chatContainer = document.querySelector('[class*="messages"]') ||
                        document.querySelector('[class*="chat-content"]') ||
                        document.querySelector('main');
  
  if (chatContainer) {
    messageObserver.observe(chatContainer, {
      childList: true,
      subtree: true
    });
  }
});

// ============================================
// KEYBOARD SHORTCUTS
// ============================================
document.addEventListener('keydown', (e) => {
  // Ctrl/Cmd + K = Focus search (if available)
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault();
    const searchInput = document.querySelector('input[type="search"]') ||
                        document.querySelector('input[placeholder*="search"]');
    if (searchInput) {
      searchInput.focus();
    }
  }
  
  // Escape = Clear input
  if (e.key === 'Escape') {
    const input = document.querySelector('textarea') || 
                  document.querySelector('#chat-input');
    if (input && document.activeElement === input) {
      input.blur();
    }
  }
});

// ============================================
// PROVIDER BADGE ANIMATION
// ============================================
function animateProviderBadge() {
  const badges = document.querySelectorAll('[class*="provider-badge"], [class*="badge"]');
  badges.forEach(badge => {
    badge.addEventListener('mouseenter', () => {
      badge.style.transform = 'scale(1.05)';
      badge.style.transition = 'transform 0.2s ease';
    });
    badge.addEventListener('mouseleave', () => {
      badge.style.transform = 'scale(1)';
    });
  });
}

// Run on DOM ready
document.addEventListener('DOMContentLoaded', animateProviderBadge);

// ============================================
// TYPING INDICATOR (Optional)
// ============================================
function showTypingIndicator() {
  const indicator = document.createElement('div');
  indicator.className = 'typing-indicator';
  indicator.innerHTML = `
    <div class="typing-dots">
      <span></span><span></span><span></span>
    </div>
    <span>TranslateHub is thinking...</span>
  `;
  indicator.style.cssText = `
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 16px;
    color: #9CA3AF;
    font-size: 14px;
    animation: fade-in 0.3s ease;
  `;
  
  const chatContainer = document.querySelector('[class*="messages"]') ||
                        document.querySelector('[class*="chat-content"]');
  if (chatContainer) {
    chatContainer.appendChild(indicator);
    scrollToBottom();
  }
  
  return indicator;
}

function hideTypingIndicator(indicator) {
  if (indicator && indicator.parentNode) {
    indicator.style.opacity = '0';
    indicator.style.transition = 'opacity 0.3s ease';
    setTimeout(() => indicator.remove(), 300);
  }
}

// ============================================
// LANGUAGES BUTTON & DROPDOWN
// ============================================
const SUPPORTED_LANGUAGES = [
  { name: "English",   flag: "🇬🇧" },
  { name: "Urdu",      flag: "🇵🇰" },
  { name: "Arabic",    flag: "🇸🇦" },
  { name: "French",    flag: "🇫🇷" },
  { name: "German",    flag: "🇩🇪" },
  { name: "Spanish",   flag: "🇪🇸" },
  { name: "Hindi",     flag: "🇮🇳" },
  { name: "Japanese",  flag: "🇯🇵" },
  { name: "Chinese",   flag: "🇨🇳" },
  { name: "Turkish",   flag: "🇹🇷" },
  { name: "Italian",   flag: "🇮🇹" },
  { name: "Russian",   flag: "🇷🇺" },
  { name: "Portuguese", flag: "🇧🇷" },
  { name: "Korean",    flag: "🇰🇷" },
];

function createLanguagesButton() {
  const header = document.querySelector('header') || document.querySelector('[class*="header"]');
  if (!header || document.querySelector('.languages-btn')) return;

  // Forcefully hide ALL elements containing "Readme" text in header
  header.querySelectorAll('*').forEach(el => {
    if (el.textContent.trim().toLowerCase().includes('readme') && !el.classList.contains('languages-btn')) {
      el.style.display = 'none';
      el.style.visibility = 'hidden';
      el.style.width = '0';
      el.style.height = '0';
      el.style.overflow = 'hidden';
      el.style.position = 'absolute';
      el.style.pointerEvents = 'none';
    }
  });

  // Also hide by href/aria selectors
  const readmeSelectors = [
    'a[href*="readme"]', 'a[href*="chainlit"]', 'a[href*="github"]',
    'a[href*="/readme"]', '[class*="readme"]', '[class*="Readme"]',
    '[aria-label*="readme"]', '[aria-label*="Readme"]',
    '[title*="readme"]', '[title*="Readme"]'
  ];
  readmeSelectors.forEach(sel => {
    header.querySelectorAll(sel).forEach(el => {
      el.style.display = 'none';
      el.style.visibility = 'hidden';
      el.style.width = '0';
      el.style.height = '0';
      el.style.overflow = 'hidden';
      el.style.position = 'absolute';
    });
  });

  // Find any link/button in header right area and hide it
  const allLinks = header.querySelectorAll('a, button, [role="button"]');
  allLinks.forEach(el => {
    const text = el.textContent.trim().toLowerCase();
    if (text === 'readme' || text === 'read me' || text.includes('readme')) {
      el.style.display = 'none';
      el.style.visibility = 'hidden';
      el.style.position = 'absolute';
    }
  });

  const wrapper = document.createElement('div');
  wrapper.style.position = 'relative';
  wrapper.style.display = 'inline-flex';
  wrapper.style.alignItems = 'center';

  // Button
  const btn = document.createElement('button');
  btn.className = 'languages-btn';
  btn.textContent = 'Available Languages';

  // Dropdown
  const dropdown = document.createElement('div');
  dropdown.className = 'languages-dropdown';
  dropdown.style.display = 'none';

  let langItems = SUPPORTED_LANGUAGES.map(lang =>
    `<li><span class="lang-flag">${lang.flag}</span>${lang.name}</li>`
  ).join('');

  dropdown.innerHTML = `
    <h3>Supported Languages</h3>
    <ul>${langItems}</ul>
    <div class="dropdown-footer">Type any language name to start translating</div>
  `;

  // Click language -> send to chat input
  dropdown.querySelectorAll('li').forEach((li, i) => {
    li.addEventListener('click', () => {
      const langName = SUPPORTED_LANGUAGES[i].name;
      const input = document.querySelector('textarea') || document.querySelector('#chat-input');
      if (input) {
        const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value')?.set;
        if (setter) setter.call(input, langName);
        else input.value = langName;
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.focus();
      }
      dropdown.style.display = 'none';
    });
  });

  // Toggle dropdown
  btn.addEventListener('click', (e) => {
    e.stopPropagation();
    dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
  });

  // Close on outside click
  document.addEventListener('click', (e) => {
    if (!wrapper.contains(e.target)) dropdown.style.display = 'none';
  });

  wrapper.appendChild(btn);
  wrapper.appendChild(dropdown);

  // Find README-like element in header and insert BEFORE it
  const allEls = Array.from(header.querySelectorAll('a, button, [role="button"], svg'));
  let readmeEl = null;
  for (const el of allEls) {
    const text = (el.textContent || '').trim().toLowerCase();
    const href = el.getAttribute('href') || '';
    if (text.includes('readme') || href.includes('readme') || href.includes('chainlit') || href.includes('github')) {
      readmeEl = el;
      break;
    }
  }

  if (readmeEl) {
    readmeEl.parentNode.insertBefore(wrapper, readmeEl);
  } else {
    // Fallback: insert at end of header
    header.appendChild(wrapper);
  }
}

// Run when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  setTimeout(createLanguagesButton, 500);
  // Retry if header loads late
  setTimeout(createLanguagesButton, 1500);
  setTimeout(createLanguagesButton, 3000);

  // Force remove borders from welcome message
  setTimeout(removeWelcomeBorders, 500);
  setTimeout(removeWelcomeBorders, 1500);
  setTimeout(removeWelcomeBorders, 3000);
});

function removeWelcomeBorders() {
  document.querySelectorAll('[class*="message"]').forEach(msg => {
    if (msg.querySelector('.welcome-header') || msg.querySelector('.welcome-logo') || msg.querySelector('.welcome-title')) {
      const styles = 'background: transparent !important; border: none !important; box-shadow: none !important; backdrop-filter: none !important;';
      msg.style.cssText = styles;
      msg.querySelectorAll('[class*="content"], [class*="avatar"]').forEach(el => {
        el.style.cssText = styles;
      });
    }
  });
}

// ============================================
// INIT
// ============================================
console.log('%c TranslateHub %c Premium AI Translator ', 
  'background: linear-gradient(135deg, #4F8CFF, #7C3AED); color: white; padding: 8px 12px; border-radius: 6px 0 0 6px; font-weight: bold;',
  'background: #111827; color: #9CA3AF; padding: 8px 12px; border-radius: 0 6px 6px 0;'
);
