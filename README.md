# RuneHits

Hitsplats no estilo Old School RuneScape para WoW Forever (Interface 16001): o dano aparece em cima do mob, com som.

- vermelho: hit · azul com 0: miss · raios dourados: crítico
- hits juntos ocupam as posições do OSRS: centro, acima, abaixo à esquerda, abaixo à direita
- esconde os números do próprio jogo enquanto está ligado (`/rh blizz` traz de volta)

## Instalar

Copie esta pasta para `World of Warcraft\_forever_\Interface\AddOns\RuneHits` (o nome da pasta tem que ser `RuneHits`;
se baixou o zip, renomeie `RuneHits-main`).

## Comandos

`/rh` liga/desliga · `/rh teste` · `/rh som` · `/rh fonte 15` · `/rh escala 1.2` · `/rh corpo 40` (distância abaixo
da nameplate) · `/rh eu -20` · `/rh blizz` · `/rh debug`

Precisa das nameplates de inimigos ligadas para o dano ficar em cima do mob.

## Arte e sons

Tudo feito do zero, sem arquivos do jogo: `py make_runehits_art.py` desenha os splats e a fonte dos números,
`py make_runehits_sounds.py` sintetiza os sons. Para trocar um som, coloque seu próprio `.ogg` em `sounds/` com o
mesmo nome. Teste: `py test_runehits.py` (precisa de `pip install lupa`).

Projeto de fã, sem ligação com a Jagex ou a Blizzard.
