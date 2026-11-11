[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Introduction
This is a plugin for [InvenTree](https://github.com/inventree/InvenTree/).
Installing this plugin enables the automatic generation of Internal Part Numbers (IPN) for parts.

## Installation
To automatically install the plugin when running `invoke install`:
Add `inventree-ipn-generator` to your plugins.txt file.

Or, install the plugin manually:

```
pip install inventree-ipn-generator
```

For the plugin to be listed as available, you need to enable "Event Integration" in your plugin settings.
This setting is located with the Plugin Settings on the settings page.

## Settings

- Active - Enables toggling of plugin without having to disable it
- On Create - If on, the plugin will assign IPNs to newly created parts
- On Change - If on, the plugin will assign IPNs to parts after a change has been made. Enabling this setting will remove the ability to have parts without IPNs.

## Operation
The IPN pattern comes either from the PATTERN setting on the plugin, or from a category parameter called "IPN Pattern".  If a category has an "IPN Pattern" parameter, the value of the parameter is used as the pattern for parts in that category, or in its subcategories, unless one of them also has an "IPN Pattern" parameter.

IPNs are generated when a part is saved after editing or creation, if settings allow.

IPNs are only generated if the IPN field is empty or set to `auto`.

If "On Change" is true, IPNs are regenerated after editing, if the IPN field is empty.

The plugin will generate a new IPN if the IPN field is set to `auto`, even if "On Change" is false.

When an IPN is generated, the plugin searches for an unused IPN by starting from the lowest IPN allowed by the pattern, and incrementing until it finds an IPN which is unique.  Note that if a part is completely deleted, its IPN may be reused.  If you do not want this, do not delete the part, but instead mark it inactive.

## Patterns
Patterns are a list of parts, which may be literal, numeric, or character.  Numeric and character parts can be incremented; literal parts are static.

Part numbers are incremented beginning with the rightmost part, continuing leftward until an increment does not result in a wraparound (carry).

If all parts in the number are incremented, and the leftmost part carries, the *entire* part number cycle wraps around and begins from the first number.  This may result in errors if duplicate IPNs are not allowed.

### Literals (Immutable)

Any part of the pattern outside `{}`, `[]`, or `()` is static and unchanged. Text inside parentheses (`()`) is also static and unchanged.

Example: `(A6C)` will _always_ render as "A6C", regardless of other groups

### Numeric
Numbers that should change over time should be encased in `{}`
- `{5}` respresents a number with exactly 5 digits, zero-padded.
- `{25+}` represents a number 25-99
- `{4:99..899}` is a range of numbers from 99 to 899 inclusive, displayed as a 4-digit zero-padded number.

Example: `{5+}{3}` will result in this range: 5000-9999

### Characters
Characters that change should be encased in `[]`
- `[abc]` cycles through the letters `a`, `b`, `c` in order.
- `[a-f]` cycles through the letters `a` to `f`
- `[A-F]` cycles through the letters `A` to `F`

### Examples
1. `(AB){3}[ab]` -> AB001a, AB001b, AB002a, AB021b, AB032a, etc
2. `{2}[Aq](BD)` -> 01ABD, 01qBD, 02ABD, 02qBD, etc
3. `{1}[a-d]{8+}` -> 1a8, 1a9, 1b8, 1b9, 1c8, 1c9, 1d8, 1d9, 2a8, etc
