from acceptance_runner import Chapter
with Chapter('ch11') as c:
    c.probe('05-project','mlp','proba[:]=.1')
    c.probe('05-project','errors','cm[:]=0')
    c.probe('05-project','errors','queue_knn=queue_knn[:-1]')
    c.probe('05-project','own-net','own_proba[:]=.1')
    c.probe('03-mlp','alpha-sweep',expected=True)

    c.probe('05-project','look',expected=True)
    source=c.tasks['05-project','look']['solution']
    c.probe('05-project','look',code=source.replace('ax.imshow(mean_imgs[k], cmap="gray_r")','ax.matshow(mean_imgs[k]/16, cmap="gray_r")'),expected=True)
    c.probe('05-project','look',code=source.replace('ax.imshow(mean_imgs[k], cmap="gray_r")','plt.sca(ax)\n    plt.imshow(mean_imgs[k],cmap="gray")'),expected=True)
    c.probe('05-project','look',code=source.replace('ax.imshow(mean_imgs[k], cmap="gray_r")','pass'))
    c.probe('05-project','look',code=source.replace('ax.imshow(mean_imgs[k], cmap="gray_r")','ax.imshow(mean_imgs[3],cmap="gray_r")'))
    c.probe('05-project','look',code=source.replace('ax.imshow(mean_imgs[k], cmap="gray_r")','ax.imshow(mean_imgs[9-k],cmap="gray_r")'))
    c.probe('05-project','look',code=source.replace('ax.set_title(str(k))','ax.set_title(str(9-k))'))
    c.probe('05-project','look',code=source.replace('ax.set_title(str(k))','ax.set_title("3")'))
    c.probe('05-project','look','mean_imgs[0]=0')
    c.probe('05-project','look','axes[5].images[0].set_visible(False)')
    c.probe('05-project','look','axes[5].images[0].set_alpha(0)')
    c.probe('05-project','look',code=source.replace('plt.subplots(1, 10, figsize=(10, 1.4))','plt.subplots(2, 5, figsize=(10, 3))').replace('enumerate(axes)','enumerate(axes.ravel())'))

    # The original shift solution remains a positive compatibility case.
    c.probe('05-project','shift',expected=True)
    c.probe('05-project','blur-transfer',expected=True)
    source=c.tasks['05-project','blur-transfer']['solution']
    confidence=source.replace('rule_name="margin"','rule_name="confidence"').replace('score=top[:,-1]-top[:,-2]','score=top[:,-1]')
    c.probe('05-project','blur-transfer',code=confidence,expected=True)
    last_error=source.replace('))[0])', '))[-1])')
    c.probe('05-project','blur-transfer',code=last_error,expected=True)
    c.probe('05-project','blur-transfer','missed_errors=0')
    c.probe('05-project','blur-transfer','queue=queue[::-1]')
    c.probe('05-project','blur-transfer','rule_name="confidence"')
    c.probe('05-project','blur-transfer','phone_accuracy=1-missed_errors/len(final_labels)')
    c.probe('05-project','blur-transfer','evaluation_unit="phone"')
    c.probe('05-project','blur-transfer','final_labels=np.zeros_like(final_labels)')
    c.probe('05-project','blur-transfer','phone_note=""')

    # Gate errors must happen before final labels are returned, rather than only at grading.
    import harness
    def gate_rejects(code,message):
        item=c.tasks['05-project','blur-transfer']
        result=harness.run(code,item['check'],item['setup'],False)
        assert not result['ok'], result
        assert message in result['error']['text'], result
        print('OK blur-transfer gate rejected before labels; '+message)
    gate_rejects('final_labels=open_blur_labels({},"margin",list(range(37)),"Обоснованное правило до меток")','В example нет поля')
    gate_rejects(source.replace('queue,rule_reason)', 'queue[:-1],rule_reason)'), 'ровно 37 разных')
    gate_rejects(source.replace('queue,rule_reason)', 'queue[::-1],rule_reason)'), 'не соответствует записанному правилу')
    gate_rejects(source.replace('fig,ax=plt.subplots()', 'fig,ax=plt.subplots()').replace('ax.imshow(validation["images"][i],cmap="gray")','pass'), 'покажите размытое изображение')
    # Once labels have been returned, another rule cannot be opened in the same attempt.
    gate_rejects(source+'\nother=np.argsort(blind["proba"].max(1),kind="stable")[:37].tolist()\nopen_blur_labels(example,"confidence",other,rule_reason)', 'уже открыты')
    gate_rejects('_blur_assessment()', 'Сначала зафиксируйте')

    # Literal captions from the student's blur-and-look-retest.md: both mean the same.
    title_line='ax.set_title(f"Позиция {i}; истина {example[\'truth\']}; прогноз {example[\'prediction\']}; p={example[\'confidence\']:.2f}")'
    english_title='ax.set_title(f"position=55; truth={example["truth"]}; prediction={example["prediction"]}; confidence={example["confidence"]:.3f}")'
    russian_title='ax.set_title("Позиция 55; истина 6; прогноз 4; p=0.98")'
    assert title_line in source
    c.probe('05-project','blur-transfer',code=source.replace(title_line,english_title),expected=True)
    c.probe('05-project','blur-transfer',code=source.replace(title_line,russian_title),expected=True)
    percent_title='ax.set_title(f"ID: {i} / true: {example[\'truth\']} / pred: {example[\'prediction\']} / confidence: {100*example[\'confidence\']:.1f}%")'
    c.probe('05-project','blur-transfer',code=source.replace(title_line,percent_title),expected=True)
    for bad_title,field in [
        ('position=56; truth=6; prediction=4; confidence=.981','position/позиция'),
        ('position=55; truth=4; prediction=6; confidence=.981','truth/истина'),
        ('position=55; truth=6; prediction=6; confidence=.981','prediction/прогноз'),
        ('position=55; truth=6; prediction=4; confidence=.90','confidence/уверенность'),
        ('position=55; truth=6; prediction=4','confidence/уверенность'),
        ('55; 6; 4; .981','position/позиция'),
        ('position=55; truth=6; prediction=4; confidence=.981; truth=4','truth/истина'),
    ]:
        gate_rejects(source.replace(title_line,'ax.set_title('+repr(bad_title)+')'),field)
