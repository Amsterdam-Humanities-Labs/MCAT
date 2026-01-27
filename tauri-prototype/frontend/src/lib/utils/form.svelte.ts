/**
 * Generic form validation system for Svelte 5
 *
 * Usage:
 * ```ts
 * const form = new FormState({
 *   name: { value: '', rules: [required('Name is required')] },
 *   email: { value: '', rules: [required(), email()] },
 * });
 *
 * // In template:
 * <Input value={form.fields.name.value} error={form.fields.name.error} />
 * <Button disabled={!form.valid} onclick={() => { form.touchAll(); if (form.valid) submit(); }}>
 * ```
 */

export type ValidationRule<T> = (value: T) => string | null;

// Built-in validation rules
export const rules = {
  required:
    (message = 'This field is required'): ValidationRule<string> =>
    (value) =>
      !value || value.trim() === '' ? message : null,

  minLength:
    (min: number, message?: string): ValidationRule<string> =>
    (value) =>
      value && value.length < min
        ? message ?? `Must be at least ${min} characters`
        : null,

  maxLength:
    (max: number, message?: string): ValidationRule<string> =>
    (value) =>
      value && value.length > max
        ? message ?? `Must be at most ${max} characters`
        : null,

  pattern:
    (regex: RegExp, message = 'Invalid format'): ValidationRule<string> =>
    (value) =>
      value && !regex.test(value) ? message : null,

  email:
    (message = 'Invalid email address'): ValidationRule<string> =>
    (value) =>
      value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value) ? message : null,

  url:
    (message = 'Invalid URL'): ValidationRule<string> =>
    (value) => {
      if (!value) return null;
      try {
        new URL(value);
        return null;
      } catch {
        return message;
      }
    },

  selected:
    (message = 'Please select an option'): ValidationRule<string> =>
    (value) =>
      !value ? message : null,
};

type FieldConfig<T> = {
  value: T;
  rules?: ValidationRule<T>[];
};

type FieldState<T> = {
  value: T;
  error: string | null;
  touched: boolean;
};

// Extract value type from field config
type ExtractValue<T> = T extends FieldConfig<infer V> ? V : never;

// Map config to field states
type FieldStates<T extends Record<string, FieldConfig<string>>> = {
  [K in keyof T]: FieldState<ExtractValue<T[K]>>;
};

// Map config to just values
type FieldValues<T extends Record<string, FieldConfig<string>>> = {
  [K in keyof T]: ExtractValue<T[K]>;
};

/**
 * Reactive form state manager
 */
export class FormState<T extends Record<string, FieldConfig<string>>> {
  #fields: FieldStates<T> = $state({} as FieldStates<T>);
  #config: T;
  #allTouched = $state(false);

  constructor(config: T) {
    this.#config = config;

    // Initialize fields
    const initial = {} as FieldStates<T>;
    for (const key of Object.keys(config) as (keyof T)[]) {
      (initial as Record<keyof T, FieldState<string>>)[key] = {
        value: config[key].value,
        error: null,
        touched: false,
      };
    }
    this.#fields = initial;
  }

  /** Get all field states */
  get fields(): FieldStates<T> {
    // Recompute errors based on current values and touched state
    const result = {} as FieldStates<T>;

    for (const key of Object.keys(this.#config) as (keyof T)[]) {
      const field = this.#fields[key];
      const config = this.#config[key];
      const shouldShowError = field.touched || this.#allTouched;

      let error: string | null = null;
      if (shouldShowError && config.rules) {
        for (const rule of config.rules) {
          error = rule(field.value);
          if (error) break;
        }
      }

      (result as Record<keyof T, FieldState<string>>)[key] = {
        value: field.value,
        error,
        touched: field.touched || this.#allTouched,
      };
    }

    return result;
  }

  /** Check if form is valid (all fields pass validation) */
  get valid(): boolean {
    for (const key of Object.keys(this.#config) as (keyof T)[]) {
      const field = this.#fields[key];
      const config = this.#config[key];

      if (config.rules) {
        for (const rule of config.rules) {
          if (rule(field.value)) return false;
        }
      }
    }
    return true;
  }

  /** Set a field's value */
  setValue<K extends keyof T>(key: K, value: ExtractValue<T[K]>): void {
    (this.#fields as Record<K, FieldState<string>>)[key] = {
      ...this.#fields[key],
      value,
    };
  }

  /** Get a field's current value */
  getValue<K extends keyof T>(key: K): ExtractValue<T[K]> {
    return this.#fields[key].value;
  }

  /** Mark a field as touched (will show errors) */
  touch(key: keyof T): void {
    (this.#fields as Record<keyof T, FieldState<string>>)[key] = {
      ...this.#fields[key],
      touched: true,
    };
  }

  /** Mark all fields as touched (call on submit attempt) */
  touchAll(): void {
    this.#allTouched = true;
  }

  /** Reset form to initial values */
  reset(): void {
    this.#allTouched = false;
    for (const key of Object.keys(this.#config) as (keyof T)[]) {
      (this.#fields as Record<keyof T, FieldState<string>>)[key] = {
        value: this.#config[key].value,
        error: null,
        touched: false,
      };
    }
  }

  /** Get all current values as an object */
  getValues(): FieldValues<T> {
    const result = {} as FieldValues<T>;
    for (const key of Object.keys(this.#config) as (keyof T)[]) {
      (result as Record<keyof T, string>)[key] = this.#fields[key].value;
    }
    return result;
  }
}
