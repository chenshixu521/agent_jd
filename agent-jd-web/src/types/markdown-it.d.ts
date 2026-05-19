declare module 'markdown-it' {
  interface MarkdownItOptions {
    html?: boolean
    linkify?: boolean
    breaks?: boolean
  }

  export default class MarkdownIt {
    constructor(options?: MarkdownItOptions)
    render(content: string): string
  }
}
