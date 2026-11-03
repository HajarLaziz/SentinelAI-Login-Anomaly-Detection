"""Execute all notebook cells using this environment's Python kernel."""
import os
import asyncio
from pathlib import Path
import nbformat
from nbclient import NotebookClient
from jupyter_client.kernelspec import KernelSpecManager
from ipykernel.kernelspec import write_kernel_spec

if os.name == 'nt':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

root = Path(__file__).resolve().parents[1]
runtime = root/'artifacts'/'jupyter'
runtime.mkdir(parents=True,exist_ok=True)
os.environ['JUPYTER_RUNTIME_DIR'] = str(runtime)
kernel = runtime/'kernels'/'sentinelai'
if not kernel.exists():
    write_kernel_spec(str(kernel))
manager = KernelSpecManager(kernel_dirs=[str(kernel.parent)])
nb = nbformat.read(root/'notebooks'/'anomaly_detection_explained.ipynb',as_version=4)
client = NotebookClient(nb,timeout=180,kernel_name='sentinelai',resources={'metadata':{'path':str(root)}})
client.create_kernel_manager()
client.km.kernel_spec_manager = manager
client.execute()
nbformat.write(nb,root/'artifacts'/'anomaly_detection_explained.executed.ipynb')
print(f'Notebook exécuté : {sum(c.cell_type=="code" for c in nb.cells)} cellules de code, aucune erreur.')
