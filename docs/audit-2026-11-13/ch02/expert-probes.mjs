/* Run from the repository root after exporting tasks with tools/build.py --export. */
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { pathToFileURL } from 'node:url'

const read = name => readFileSync(resolve(name), 'utf8')
const entries = JSON.parse(read(process.argv[2]))
const directory = resolve('site/assets/vendor/pyodide') + '/'
const { loadPyodide } = await import(pathToFileURL(directory + 'pyodide.mjs').href)
const py = await loadPyodide({ indexURL: directory })
await py.loadPackage(['pandas', 'duckdb'], { messageCallback() {} })
py.FS.writeFile('/home/pyodide/_dsc_harness.py', read('site/assets/harness.py'))
py.runPython('import sys; sys.path.insert(0, "/home/pyodide"); import _dsc_harness')
const run = py.pyimport('_dsc_harness').run
console.log('runtime', py.version, process.version, py.runPython('import pandas, duckdb, numpy; (sys.version.split()[0], pandas.__version__, duckdb.__version__, numpy.__version__)').toJs())

function probe(lesson, id, cases) {
    const task = entries.find(e => e.lesson === 'ch02/' + lesson && e.kind === 'task' && e.id === id)
    for (const file of task.files) {
        py.FS.writeFile('/home/pyodide/' + file, readFileSync(resolve('site/data', file)))
    }
    for (const [label, makeCode] of Object.entries(cases)) {
        const r = run(makeCode(task.solution), task.check, task.setup, true)
        const output = r.toJs({dict_converter: Object.fromEntries})
        r.destroy()
        console.log(lesson, id, label, output.check?.passed ?? false, output.check?.msg ?? output.error?.text ?? '')
    }
}
const calendar = table => '\n' + table + '["month"] = ' + table + '["month"] + pd.DateOffset(months=1)'
const q = "import duckdb\navg_check_delivery = duckdb.sql(\"SELECT ROUND(AVG(amount), 2) FROM read_csv('orders_3m.csv') WHERE channel = 'доставка'\").fetchone()[0]"
probe('07-duckdb','from-file',{
    'correct-direct-read_csv': () => q,
    'correct-direct-path': code => code,
    'wrong-channel': code => code.replaceAll('доставка','зал'),
})
probe('09-project','monthly',{
    'correct-groupby': code => code,
    'wrong-units-as-orders': code => code + '\nmonthly["orders"] = full.groupby(full.datetime.dt.to_period("M")).qty.sum()\nmonthly["avg_check"] = (monthly.revenue / monthly.orders).round(1)',
})
probe('09-project','shops',{
    'correct-index': code => code,
    'wrong-revenue-in-thousands': code => code + '\nby_shop["revenue"] = by_shop.revenue / 1000',
})
probe('09-project','heatmap',{
    'correct-crosstab': () => 'import pandas as pd\nload = pd.crosstab(full.datetime.dt.weekday, full.datetime.dt.hour)\npeak = load.stack().idxmax()',
    'wrong-cups': () => 'load = full.groupby([full.datetime.dt.weekday.rename("weekday"), full.datetime.dt.hour.rename("hour")]).qty.sum().unstack()\npeak = load.stack().idxmax()',
    'wrong-percent-units': () => 'import pandas as pd\nload = pd.crosstab(full.datetime.dt.weekday, full.datetime.dt.hour, normalize="all") * 100\npeak = load.stack().idxmax()',
})
for (const [id,table,col] of [['p-city-month','city_month','month'],['p-promo','promo_items','month'],['p-cohorts','ret','cohort']]) {
    probe('11-sql-project', id,{
        'correct-reference': code => code,
        'wrong-month-shift': code => code + '\nimport pandas as pd' + calendar(table).replaceAll('"month"','"' + col + '"'),
    })
}
probe('09-project','verdicts',{
    'correct-five-calls': code => code,
    'correct-comprehension': code => code.replaceAll('verdicts = {}','conditions = {}').replace(/^verdicts\["(H\d)"\] = verdict\((.*)\)$/gm,'conditions["$1"] = $2').replace(/\nverdicts\s*$/,'\nverdicts = {k: verdict(v) for k, v in conditions.items()}'),
})
probe('09-project','load',{
    'correct-merges': code => code,
    'wrong-positional-assignment': () => 'import pandas as pd\nfull = pd.read_csv("orders_3m.csv", parse_dates=["datetime"])\nshops = pd.read_csv("shops.csv")\nmenu = pd.read_csv("menu.csv")\nfull[["city","seats"]] = shops[["city","seats"]]\nfull[["category","cost_s"]] = menu[["category","cost_s"]]\nsame_rows = len(full) == len(pd.read_csv("orders_3m.csv"))',
})
