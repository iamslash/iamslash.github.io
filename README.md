# iamslash.github.io

Personal site built with [mdBook](https://rust-lang.github.io/mdBook/).

## Local Development

```bash
# Install mdBook
cargo install mdbook

# Serve locally (http://localhost:3000)
mdbook serve

# Build
mdbook build
```

## Deployment

Pushes to `main` automatically build and deploy to GitHub Pages via GitHub Actions.
