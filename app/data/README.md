# 📦 Data & Playground Examples

This directory contains structured JSON data for:
- ✅ Production-like test records
- 🎮 Interactive learning playground examples
- 🧪 Edge cases & invalid inputs for validation testing

## 📁 File Structure
| File | Purpose |
|------|---------|
| `data.json` | Valid, production-ready records covering all models |
| `playground_examples.json` | Categorized valid/invalid payloads for interactive learning |
| `README.md` | This documentation |

## 🎮 Playground Usage
The interactive frontend fetches `playground_examples.json` to:
1. Populate JSON editors with working examples
2. Show "invalid" cases to demonstrate error messages
3. Map model names to test payloads for `/lab/playground/validate`

## 🔍 Data Coverage
- `user_basic`: Standard user records with nested address
- `user_enums`: Records with StrEnum fields & computed field sources
- `order`: E-commerce orders for pricing calculations
- `comment_thread`: Recursive nested comments
- `payment_profile`: Discriminated union payment methods
- `notification_config`: Nested union notification channels

## 🧪 Invalid Case Testing
Use the `invalid` keys in `playground_examples.json` to:
- Test field constraint errors
- Demonstrate `strict=True` vs lenient behavior
- Show computed field dependencies
- Practice error handling in frontend

## 🔒 Security Note
- API keys in `data.json` are **dummy/test values only**
- Never use real secrets in data files
- In production, use environment variables or secret managers