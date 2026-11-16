import os,runpy
os.environ['OMP_NUM_THREADS']='1';os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['MKL_NUM_THREADS']='1'
import torch
torch.set_num_threads(1);torch.set_num_interop_threads(1)
os.chdir('/private/tmp/kuch14round/student/data')
runpy.run_path('/private/tmp/kuch14round/student/extra/cnn-visible-example.py',run_name='__main__')
