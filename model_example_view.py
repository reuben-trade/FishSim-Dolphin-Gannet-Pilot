"""Optional position view of completed short examples; never runs a model."""
from pathlib import Path
import json
import numpy as np
import matplotlib.pyplot as plt


def show_position_snapshot(output):
    folders=sorted((Path(output)/'cases').glob('*'))
    if len(folders)!=2:
        raise ValueError('Expected the completed matched D-only/DG example pair')
    fig,axes=plt.subplots(1,2,figsize=(10,4),sharex=True,sharey=True)
    for ax,folder in zip(axes,folders):
        if json.loads((folder/'completion.json').read_text())['status']!='complete':
            raise ValueError('Only completed example snapshots may be displayed')
        config=json.loads((folder/'config.json').read_text())
        with np.load(folder/'trajectories.npz',allow_pickle=False) as data:
            alive=data['alive'][-1].astype(bool)
            fish=data['positions'][-1,alive]
            actors=data['predator_positions'][-1]
            ids=data['actor_ids'].astype(str)
            ax.scatter(fish[:,0],fish[:,1],s=7,c='#8099AB',label='Live fish')
            for prefix,colour,label in [('D','#087F8C','Dolphins'),('G','#D98525','Gannets')]:
                selected=np.char.startswith(ids,prefix)
                if selected.any():ax.scatter(actors[selected,0],actors[selected,1],s=30,c=colour,label=label)
            elapsed=float(data['time'][-1]-data['time'][0])
            ax.set_title(f"{config['presence']}: {elapsed:g}T top-view snapshot")
        ax.set(xlabel='Model x',ylabel='Model y',aspect='equal')
        ax.legend(fontsize=8)
    fig.suptitle('Short execution example; no feeding-benefit inference')
    fig.tight_layout()
    plt.show()
    return fig
