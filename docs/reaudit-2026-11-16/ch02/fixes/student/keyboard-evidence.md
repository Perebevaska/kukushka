# Проверка горячих клавиш в настоящем JupyterLab

- [x] Запущен JupyterLab из /private/tmp/ku-audit/nb-env на loopback, отдельный тестовый блокнот.
- [x] Из редактора нажаты Esc → B → M: UI показал Cell 2/2 и тип Markdown.
- [x] Enter → ввод текста → Shift+Enter: UI перешёл к следующей Code-ячейке.
- [x] Cmd+S, Rename and Save: keyboard-practice.ipynb сохранён через UI.
- [x] Итоговый JSON: Code, Markdown, Code; Markdown имеет source/id/metadata и не имеет outputs/execution_count.
- [x] Штатный экспорт nbconvert --to html --no-input в keyboard-practice.html.
- [x] В Safari визуально увидены заголовок Keyboard practice и полный абзац Conclusion в HTML. Подтверждено screenshot последнего CUA-вызова «Подтверждаю отрисованный HTML».

Ограничения: Chrome через native CUA не открылся (timeout). В JupyterLab Safari видел source, смену типов и сохранение; AX после reload содержал отрисованный текст, но screenshot показывал спиннер. Поэтому видимый результат заявлен для экспортированного HTML, не для самого полотна JupyterLab. Никакой программной подстановки Markdown в тестовый ipynb не было: его содержимое создано UI-действиями.
