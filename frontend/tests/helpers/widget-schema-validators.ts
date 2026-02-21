/**
 * Widget Schema Validators
 *
 * Validates that API responses match frontend TypeScript interfaces.
 * Used by contract tests to catch schema drift between frontend and backend.
 *
 * @see frontend/src/widget/types/widget.ts
 */

export const validateHexColor = (value: unknown): boolean => {
  if (typeof value !== 'string') return false;
  return /^#[0-9a-fA-F]{6}$/.test(value);
};

export const validateISODateString = (value: unknown): boolean => {
  if (typeof value !== 'string') return false;
  const date = new Date(value);
  return !isNaN(date.getTime()) && value.includes('T');
};

export const validateUUID = (value: unknown): boolean => {
  if (typeof value !== 'string') return false;
  return /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/.test(value);
};

export interface SchemaValidationError {
  path: string;
  expected: string;
  received: unknown;
}

export class SchemaValidator {
  private errors: SchemaValidationError[] = [];

  validate(value: unknown, validator: (v: unknown) => boolean, path: string, expected: string): boolean {
    if (!validator(value)) {
      this.errors.push({ path, expected, received: value });
      return false;
    }
    return true;
  }

  getErrors(): SchemaValidationError[] {
    return this.errors;
  }

  hasErrors(): boolean {
    return this.errors.length > 0;
  }

  reset(): void {
    this.errors = [];
  }
}

export const WidgetThemeSchema = {
  validate(theme: unknown, validator: SchemaValidator): boolean {
    if (typeof theme !== 'object' || theme === null) {
      validator.errors.push({ path: 'theme', expected: 'object', received: typeof theme });
      return false;
    }

    const t = theme as Record<string, unknown>;
    let valid = true;

    if (!validateHexColor(t.primaryColor)) {
      validator.errors.push({ path: 'theme.primaryColor', expected: 'hex color', received: t.primaryColor });
      valid = false;
    }
    if (!validateHexColor(t.backgroundColor)) {
      validator.errors.push({ path: 'theme.backgroundColor', expected: 'hex color', received: t.backgroundColor });
      valid = false;
    }
    if (!validateHexColor(t.textColor)) {
      validator.errors.push({ path: 'theme.textColor', expected: 'hex color', received: t.textColor });
      valid = false;
    }
    if (!validateHexColor(t.botBubbleColor)) {
      validator.errors.push({ path: 'theme.botBubbleColor', expected: 'hex color', received: t.botBubbleColor });
      valid = false;
    }
    if (!validateHexColor(t.userBubbleColor)) {
      validator.errors.push({ path: 'theme.userBubbleColor', expected: 'hex color', received: t.userBubbleColor });
      valid = false;
    }
    if (typeof t.position !== 'string' || !['bottom-right', 'bottom-left'].includes(t.position)) {
      validator.errors.push({ path: 'theme.position', expected: 'bottom-right | bottom-left', received: t.position });
      valid = false;
    }
    if (typeof t.borderRadius !== 'number' || t.borderRadius < 0 || t.borderRadius > 30) {
      validator.errors.push({ path: 'theme.borderRadius', expected: 'number 0-30', received: t.borderRadius });
      valid = false;
    }
    if (typeof t.width !== 'number' || t.width < 280 || t.width > 500) {
      validator.errors.push({ path: 'theme.width', expected: 'number 280-500', received: t.width });
      valid = false;
    }
    if (typeof t.height !== 'number' || t.height < 400 || t.height > 800) {
      validator.errors.push({ path: 'theme.height', expected: 'number 400-800', received: t.height });
      valid = false;
    }
    if (typeof t.fontFamily !== 'string') {
      validator.errors.push({ path: 'theme.fontFamily', expected: 'string', received: typeof t.fontFamily });
      valid = false;
    }
    if (typeof t.fontSize !== 'number' || t.fontSize < 12 || t.fontSize > 20) {
      validator.errors.push({ path: 'theme.fontSize', expected: 'number 12-20', received: t.fontSize });
      valid = false;
    }

    return valid;
  },
};

export const WidgetConfigSchema = {
  validate(config: unknown, validator: SchemaValidator): boolean {
    if (typeof config !== 'object' || config === null) {
      validator.errors.push({ path: 'config', expected: 'object', received: typeof config });
      return false;
    }

    const c = config as Record<string, unknown>;
    let valid = true;

    if (typeof c.enabled !== 'boolean') {
      validator.errors.push({ path: 'config.enabled', expected: 'boolean', received: typeof c.enabled });
      valid = false;
    }
    if (typeof c.botName !== 'string') {
      validator.errors.push({ path: 'config.botName', expected: 'string', received: typeof c.botName });
      valid = false;
    }
    if (typeof c.welcomeMessage !== 'string') {
      validator.errors.push({ path: 'config.welcomeMessage', expected: 'string', received: typeof c.welcomeMessage });
      valid = false;
    }
    if (!WidgetThemeSchema.validate(c.theme, validator)) {
      valid = false;
    }
    if (c.allowedDomains !== undefined && !Array.isArray(c.allowedDomains)) {
      validator.errors.push({ path: 'config.allowedDomains', expected: 'array', received: typeof c.allowedDomains });
      valid = false;
    }

    return valid;
  },
};

export const WidgetSessionSchema = {
  validate(session: unknown, validator: SchemaValidator): boolean {
    if (typeof session !== 'object' || session === null) {
      validator.errors.push({ path: 'session', expected: 'object', received: typeof session });
      return false;
    }

    const s = session as Record<string, unknown>;
    let valid = true;

    const sessionId = s.session_id || s.sessionId;
    const expiresAt = s.expires_at || s.expiresAt;

    if (typeof sessionId !== 'string' || sessionId.length < 10) {
      validator.errors.push({ path: 'session.sessionId', expected: 'string (min 10 chars)', received: sessionId });
      valid = false;
    }
    if (expiresAt && !validateISODateString(expiresAt)) {
      validator.errors.push({ path: 'session.expiresAt', expected: 'ISO date string', received: expiresAt });
      valid = false;
    }

    return valid;
  },
};

export const WidgetCartSchema = {
  validate(cart: unknown, validator: SchemaValidator): boolean {
    if (typeof cart !== 'object' || cart === null) {
      validator.errors.push({ path: 'cart', expected: 'object', received: typeof cart });
      return false;
    }

    const c = cart as Record<string, unknown>;
    let valid = true;

    if (!Array.isArray(c.items)) {
      validator.errors.push({ path: 'cart.items', expected: 'array', received: typeof c.items });
      valid = false;
    } else {
      c.items.forEach((item: unknown, index: number) => {
        if (typeof item !== 'object' || item === null) {
          validator.errors.push({ path: `cart.items[${index}]`, expected: 'object', received: typeof item });
          valid = false;
          return;
        }

        const i = item as Record<string, unknown>;
        if (typeof i.variant_id !== 'string') {
          validator.errors.push({ path: `cart.items[${index}].variant_id`, expected: 'string', received: typeof i.variant_id });
          valid = false;
        }
        if (typeof i.title !== 'string') {
          validator.errors.push({ path: `cart.items[${index}].title`, expected: 'string', received: typeof i.title });
          valid = false;
        }
        if (typeof i.price !== 'number') {
          validator.errors.push({ path: `cart.items[${index}].price`, expected: 'number', received: typeof i.price });
          valid = false;
        }
        if (typeof i.quantity !== 'number' || i.quantity < 1) {
          validator.errors.push({ path: `cart.items[${index}].quantity`, expected: 'number >= 1', received: i.quantity });
          valid = false;
        }
      });
    }

    if (typeof c.item_count !== 'number' && typeof c.itemCount !== 'number') {
      validator.errors.push({ path: 'cart.itemCount', expected: 'number', received: typeof c.item_count });
      valid = false;
    }
    if (typeof c.subtotal !== 'number' && typeof c.total !== 'number') {
      validator.errors.push({ path: 'cart.subtotal', expected: 'number', received: typeof c.subtotal });
      valid = false;
    }
    if (typeof c.currency !== 'string') {
      validator.errors.push({ path: 'cart.currency', expected: 'string', received: typeof c.currency });
      valid = false;
    }

    return valid;
  },
};

export const WidgetProductSchema = {
  validate(product: unknown, validator: SchemaValidator, index = 0): boolean {
    if (typeof product !== 'object' || product === null) {
      validator.errors.push({ path: `products[${index}]`, expected: 'object', received: typeof product });
      return false;
    }

    const p = product as Record<string, unknown>;
    let valid = true;

    const id = p.id || p.product_id || p.productId;
    const variantId = p.variant_id || p.variantId;
    const imageUrl = p.image_url || p.imageUrl;
    const productType = p.product_type || p.productType;

    if (typeof id !== 'string') {
      validator.errors.push({ path: `products[${index}].id`, expected: 'string', received: typeof id });
      valid = false;
    }
    if (variantId !== undefined && typeof variantId !== 'string') {
      validator.errors.push({ path: `products[${index}].variant_id`, expected: 'string', received: typeof variantId });
      valid = false;
    }
    if (typeof p.title !== 'string') {
      validator.errors.push({ path: `products[${index}].title`, expected: 'string', received: typeof p.title });
      valid = false;
    }
    if (typeof p.price !== 'number') {
      validator.errors.push({ path: `products[${index}].price`, expected: 'number', received: typeof p.price });
      valid = false;
    }
    if (p.available !== undefined && typeof p.available !== 'boolean') {
      validator.errors.push({ path: `products[${index}].available`, expected: 'boolean', received: typeof p.available });
      valid = false;
    }

    return valid;
  },
};

export const WidgetMessageSchema = {
  validate(message: unknown, validator: SchemaValidator): boolean {
    if (typeof message !== 'object' || message === null) {
      validator.errors.push({ path: 'message', expected: 'object', received: typeof message });
      return false;
    }

    const m = message as Record<string, unknown>;
    let valid = true;

    const messageId = m.message_id || m.messageId;
    const createdAt = m.created_at || m.createdAt;

    if (typeof messageId !== 'string') {
      validator.errors.push({ path: 'message.messageId', expected: 'string', received: typeof messageId });
      valid = false;
    }
    if (typeof m.content !== 'string') {
      validator.errors.push({ path: 'message.content', expected: 'string', received: typeof m.content });
      valid = false;
    }
    if (typeof m.sender !== 'string' || !['user', 'bot'].includes(m.sender as string)) {
      validator.errors.push({ path: 'message.sender', expected: 'user | bot', received: m.sender });
      valid = false;
    }
    if (!validateISODateString(createdAt)) {
      validator.errors.push({ path: 'message.createdAt', expected: 'ISO date string', received: createdAt });
      valid = false;
    }

    if (m.intent && typeof m.intent !== 'string') {
      validator.errors.push({ path: 'message.intent', expected: 'string', received: typeof m.intent });
      valid = false;
    }
    if (m.confidence && typeof m.confidence !== 'number') {
      validator.errors.push({ path: 'message.confidence', expected: 'number', received: typeof m.confidence });
      valid = false;
    }
    if (m.checkout_url && typeof m.checkout_url !== 'string') {
      validator.errors.push({ path: 'message.checkoutUrl', expected: 'string', received: typeof m.checkout_url });
      valid = false;
    }

    if (m.products && Array.isArray(m.products)) {
      m.products.forEach((p, i) => {
        if (!WidgetProductSchema.validate(p, validator, i)) {
          valid = false;
        }
      });
    }

    if (m.cart && !WidgetCartSchema.validate(m.cart, validator)) {
      valid = false;
    }

    return valid;
  },
};

export const ApiErrorResponseSchema = {
  validate(error: unknown, validator: SchemaValidator): boolean {
    if (typeof error !== 'object' || error === null) {
      validator.errors.push({ path: 'error', expected: 'object', received: typeof error });
      return false;
    }

    const e = error as Record<string, unknown>;
    let valid = true;

    if (typeof e.error_code !== 'number') {
      validator.errors.push({ path: 'error.error_code', expected: 'number', received: typeof e.error_code });
      valid = false;
    }
    if (typeof e.message !== 'string') {
      validator.errors.push({ path: 'error.message', expected: 'string', received: typeof e.message });
      valid = false;
    }

    return valid;
  },
};
