// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces
declare global {
  namespace App {
    // interface Error {}
    // interface Locals {}
    // interface PageData {}
    // interface PageState {}
    // interface Platform {}
  }
}

interface ImportMetaEnv {
  readonly PUBLIC_BOOKS_API?: string;
  readonly PUBLIC_TASKS_API?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

export {};
