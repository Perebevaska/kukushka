import numpy as np
# До исполнения: забытый минус в L=-log(sigmoid(z)) даёт численную
# производную обратного знака. Сверка с sigmoid(z)-y должна это обнаружить.
y,z,eps=1,.4,1e-5
sigmoid=lambda z:1/(1+np.exp(-z))
analytic=sigmoid(z)-y
wrong_loss=lambda z:np.log(sigmoid(z))
wrong_numeric=(wrong_loss(z+eps)-wrong_loss(z-eps))/(2*eps)
print('analytic',analytic,'wrong_numeric',wrong_numeric,'close',np.isclose(analytic,wrong_numeric,atol=1e-5))
