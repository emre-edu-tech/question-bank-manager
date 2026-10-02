# Question Bank Manager — agent notes

- Styling is Tailwind CSS v3 with a committed build artifact: `app/static/dist/output.css`
  is generated from `app/static/src/input.css` and scanned from `app/templates/**/*.html`
  and `app/static/js/**/*.js` (see `tailwind.config.js`).
- After ANY change to a template or static JS file, run `npm run build:css` and include
  the rebuilt `app/static/dist/output.css` in the change. Never skip this: Tailwind purges
  unused classes, so new markup will render unstyled without a rebuild.
- No build step runs on the production server, so the committed `output.css` must always
  be up to date with the templates.
