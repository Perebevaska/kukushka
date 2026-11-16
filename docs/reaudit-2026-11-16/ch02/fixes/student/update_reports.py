from pathlib import Path
import json,nbformat,sys
from nbclient import NotebookClient
import pandas,duckdb,matplotlib,IPython
root=Path('/private/tmp/kuch02round/student-retest')
old=Path('/private/tmp/kuch02round/student/work')
first=''.join(json.loads((root/'ch02-project-template.ipynb').read_text())['cells'][1]['source'])
versions=f'Python {sys.version.split()[0]}, pandas {pandas.__version__}, DuckDB {duckdb.__version__}, matplotlib {matplotlib.__version__}, IPython {IPython.__version__}.'
for name in ['autumn','zerno-sql']:
 nb=nbformat.read(old/(name+'.ipynb'),as_version=4)
 if name=='autumn':
  nb.cells[1].source=first
  nb.cells.insert(2,nbformat.v4.new_code_cell('import matplotlib.pyplot as plt\nfrom IPython.display import display, Markdown\nprint("matplotlib", __import__("matplotlib").__version__)'))
  nb.cells[0].source=nb.cells[0].source.replace('Python с pandas, numpy, matplotlib и IPython','Python с pandas, matplotlib и IPython')
  nb.cells[0].source+='\n\n**Файлы:** data/orders_3m.csv, data/shops.csv, data/menu.csv рядом с блокнотом; также поддерживается ../data. **Проверенное окружение:** '+versions+' Для осеннего отчёта DuckDB не требуется. Установка: `python -m pip install pandas matplotlib ipython`; для запуска в Jupyter установите `jupyterlab ipykernel`.'
 else:
  prior=nb.cells[1].source
  start=prior.index('names=')
  nb.cells[1].source=first
  nb.cells.insert(2,nbformat.v4.new_code_cell('import duckdb\nimport matplotlib.pyplot as plt\nfrom IPython.display import display, Markdown\nprint("DuckDB",duckdb.__version__)\n'+prior[start:]))
  nb.cells[0].source+='\n\n**Файлы:** data/zdb_shops.csv, zdb_menu.csv, zdb_guests.csv, zdb_promos.csv, zdb_orders.csv, zdb_items.csv. Папка data рядом с блокнотом или ../data; SQLite-файл не нужен для этого варианта. **Проверенное окружение:** '+versions+' Установка: `python -m pip install pandas duckdb matplotlib ipython jupyterlab ipykernel`.'
 for c in nb.cells:
  s=c.source
  s=s.replace('Для анализа эффективности ниже','Для сравнения продаж ниже').replace('максимум эффективности на место','максимум продаж на место').replace('H2: вместительность и лидеры','H2: вместительность и лидеры продаж')
  s=s.replace('Сравнения эффективности','Сравнения продаж').replace('На место лидирует','По общей выручке на место лидирует')
  s=s.replace('Возврат за 30 дней рассчитан только для первого заказа до августа:','Возврат в календарные дни 0–30 включительно рассчитан только для первых заказов марта–июля:')
  s=s.replace('В приложении {int(app[\'no_orders\'])} регистраций без заказа','В приложении к 31 августа {int(app[\'no_orders\'])} регистраций без заказа')
  s=s.replace("WHERE rn=1 AND ordered_at<TIMESTAMP '2026-08-01'","WHERE rn=1 AND ordered_at>=TIMESTAMP '2026-03-01' AND ordered_at<TIMESTAMP '2026-08-01'")
  c.source=s
  if c.cell_type=='code':c.outputs=[];c.execution_count=None
 if name=='autumn':
  ix=next(i for i,c in enumerate(nb.cells) if '## 4.3.' in c.source)
  nb.cells.insert(ix,nbformat.v4.new_markdown_cell('**Граница показателя.** Общая выручка на место включает доставку и заказы навынос. Она не измеряет использование мест или загрузку зала. Для загрузки нужны занятые место-часы и доступные место-часы, часы работы и длительность визитов. Дополнительная доставка увеличит per_seat даже при пустом зале.'))
  ix=next(i for i,c in enumerate(nb.cells) if '## 5. Вердикты' in c.source)
  nb.cells.insert(ix,nbformat.v4.new_markdown_cell('**Маржинальность и решение об акции.** Доля маржи на рубль выручки отвечает одному вопросу, маржа дополнительной чашки — другому. Для выбора акции нужны ожидаемый дополнительный объём, маржа в рублях и расходы на продвижение. Прохождение порога H6 не выбирает акцию автоматически.'))
 else:
  ix=next(i for i,c in enumerate(nb.cells) if '## 6. Акционные' in c.source)
  nb.cells.insert(ix,nbformat.v4.new_markdown_cell('**Окна наблюдения.** «Без заказа к 31 августа» не значит «никогда не купит». Покупка 1 сентября не видна в этой выгрузке. Для сравнения конверсии за одинаковый срок от регистрации нужны когорты с полным сроком наблюдения. Возврат back30 считается по разности календарных дат: день первого заказа — 0, любой час дня 30 включён. Выбраны полные когорты первых заказов марта–июля, а медиана включает все наблюдаемые вторые заказы, в том числе позже дня 30.'))
 path=root/'work'/(name+'.ipynb')
 nbformat.write(nb,path)
 NotebookClient(nb,timeout=180,kernel_name='python3',resources={'metadata':{'path':str(root/'work')}}).execute()
 nbformat.write(nb,path)
 print('Clean execution',name,len(nb.cells))
