/**
 * Internationalization (i18n) System
 * Supports English and Arabic with RTL support
 */

class I18n {
  constructor() {
    this.currentLanguage = localStorage.getItem('appLanguage') || 'en';
    this.translations = {};
    this.listeners = [];
    this.loadLanguage();
  }

  async loadLanguage(lang = this.currentLanguage) {
    try {
      const response = await fetch(`/frontend/translations/${lang}.json`);
      this.translations = await response.json();
      this.currentLanguage = lang;
      localStorage.setItem('appLanguage', lang);
      
      // Update document language and direction
      document.documentElement.lang = lang;
      document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
      document.body.dir = lang === 'ar' ? 'rtl' : 'ltr';
      
      // Apply RTL/LTR CSS class
      document.documentElement.className = lang === 'ar' ? 'rtl' : 'ltr';
      
      // Notify listeners
      this.notifyListeners();
      
      return this.translations;
    } catch (error) {
      console.error('Error loading language:', error);
      return this.translations;
    }
  }

  /**
   * Get a translated string
   * Usage: t('auth.login') => "Login" or "تسجيل الدخول"
   */
  t(key, defaultValue = key) {
    const keys = key.split('.');
    let current = this.translations;
    
    for (const k of keys) {
      if (current[k] === undefined) {
        return defaultValue;
      }
      current = current[k];
    }
    
    return current || defaultValue;
  }

  /**
   * Replace placeholders in translated strings
   * Usage: tf('greeting', {name: 'John'}) with "greeting": "Hello {name}"
   */
  tf(key, params = {}) {
    let text = this.t(key);
    for (const [key, value] of Object.entries(params)) {
      text = text.replace(`{${key}}`, value);
    }
    return text;
  }

  /**
   * Get current language
   */
  getLanguage() {
    return this.currentLanguage;
  }

  /**
   * Switch language
   */
  async switchLanguage(lang) {
    if (lang !== this.currentLanguage) {
      await this.loadLanguage(lang);
    }
  }

  /**
   * Check if current language is Arabic
   */
  isArabic() {
    return this.currentLanguage === 'ar';
  }

  /**
   * Register change listener
   */
  onChange(callback) {
    this.listeners.push(callback);
  }

  /**
   * Notify all listeners
   */
  notifyListeners() {
    this.listeners.forEach(callback => callback(this.currentLanguage));
  }

  /**
   * Remove all listeners
   */
  clearListeners() {
    this.listeners = [];
  }

  /**
   * Get RTL-aware CSS values
   */
  getRTL(ltrValue, rtlValue) {
    return this.isArabic() ? rtlValue : ltrValue;
  }

  /**
   * Get all translations
   */
  getAllTranslations() {
    return this.translations;
  }
}

// Create global instance
const i18n = new I18n();

/**
 * Helper function to translate in HTML elements
 * Usage in HTML: data-i18n="auth.login"
 * This function must be called after DOM loads
 */
async function updatePageTranslations() {
  const elements = document.querySelectorAll('[data-i18n]');
  elements.forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (key) {
      el.textContent = i18n.t(key);
    }
  });

  // Also handle placeholders
  const placeholders = document.querySelectorAll('[data-i18n-placeholder]');
  placeholders.forEach(el => {
    const key = el.getAttribute('data-i18n-placeholder');
    if (key) {
      el.placeholder = i18n.t(key);
    }
  });
}

/**
 * Listen for language changes
 */
i18n.onChange(() => {
  updatePageTranslations();
});
