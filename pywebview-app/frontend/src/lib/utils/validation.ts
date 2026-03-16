/**
 * Form validation utilities for Svelte 5
 */

export type ValidationRule<T> = (value: T) => string | null;

export interface FieldState {
  touched: boolean;
  error: string | null;
}

/**
 * Common validation rules
 */
export const rules = {
  required: (message = 'This field is required'): ValidationRule<string> =>
    (value) => (!value || value.trim() === '') ? message : null,

  minLength: (min: number, message?: string): ValidationRule<string> =>
    (value) => (value && value.length < min)
      ? (message ?? `Must be at least ${min} characters`)
      : null,

  maxLength: (max: number, message?: string): ValidationRule<string> =>
    (value) => (value && value.length > max)
      ? (message ?? `Must be at most ${max} characters`)
      : null,

  pattern: (regex: RegExp, message: string): ValidationRule<string> =>
    (value) => (value && !regex.test(value)) ? message : null,

  url: (message = 'Must be a valid URL'): ValidationRule<string> =>
    (value) => {
      if (!value) return null;
      try {
        new URL(value);
        return null;
      } catch {
        return message;
      }
    },
};

/**
 * Validate a value against multiple rules
 */
export function validate<T>(value: T, ...validationRules: ValidationRule<T>[]): string | null {
  for (const rule of validationRules) {
    const error = rule(value);
    if (error) return error;
  }
  return null;
}

/**
 * Create a reactive form field with validation
 */
export function createFormField<T>(initialValue: T, ...validationRules: ValidationRule<T>[]) {
  let value = $state(initialValue);
  let touched = $state(false);

  const error = $derived(touched ? validate(value, ...validationRules) : null);
  const isValid = $derived(validate(value, ...validationRules) === null);

  return {
    get value() { return value; },
    set value(v: T) { value = v; },
    get touched() { return touched; },
    get error() { return error; },
    get isValid() { return isValid; },

    touch() { touched = true; },
    reset(newValue?: T) {
      value = newValue ?? initialValue;
      touched = false;
    },
    validate() {
      touched = true;
      return isValid;
    },
  };
}

/**
 * Create a form with multiple fields
 */
export function createForm<T extends Record<string, unknown>>(
  fields: { [K in keyof T]: { initial: T[K]; rules?: ValidationRule<T[K]>[] } }
) {
  const fieldStates = Object.entries(fields).reduce((acc, [key, config]) => {
    acc[key] = createFormField(config.initial, ...(config.rules ?? []));
    return acc;
  }, {} as Record<string, ReturnType<typeof createFormField>>);

  return {
    fields: fieldStates,

    get values(): T {
      return Object.entries(fieldStates).reduce((acc, [key, field]) => {
        acc[key as keyof T] = field.value as T[keyof T];
        return acc;
      }, {} as T);
    },

    get isValid() {
      return Object.values(fieldStates).every((field) => field.isValid);
    },

    get errors() {
      return Object.entries(fieldStates).reduce((acc, [key, field]) => {
        if (field.error) acc[key] = field.error;
        return acc;
      }, {} as Record<string, string>);
    },

    validate() {
      let valid = true;
      for (const field of Object.values(fieldStates)) {
        if (!field.validate()) valid = false;
      }
      return valid;
    },

    reset() {
      for (const field of Object.values(fieldStates)) {
        field.reset();
      }
    },

    touchAll() {
      for (const field of Object.values(fieldStates)) {
        field.touch();
      }
    },
  };
}
