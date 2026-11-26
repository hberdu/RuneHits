# RuneHits

Hitsplats no estilo Old School RuneScape para WoW Forever (Interface 16001): o dano aparece logo acima da nameplate do mob, com som. Dano em área aparece em cada mob atingido, não só no alvo.

- vermelho: hit · azul com 0: miss · raios dourados: crítico
- hits juntos se empilham para cima: o primeiro, dois acima dele, um no topo
- esconde os números do próprio jogo enquanto está ligado (`/rh blizz` traz de volta)

## Instalar

Baixe `RuneHits.zip` em [Releases](https://github.com/hberdu/RuneHits/releases/latest) e extraia dentro de
`World of Warcraft\_forever_\Interface\AddOns`. Tem que ficar `AddOns\RuneHits\RuneHits.toc`.

O "Download ZIP" do botão Code também serve: a pasta `RuneHits-main` funciona como está. Só confira que ela ficou
direto em `AddOns` (o Windows às vezes cria `RuneHits-main\RuneHits-main`; nesse caso use a de dentro). Não deixe
`RuneHits` e `RuneHits-main` juntas, senão os splats aparecem duas vezes.

## Comandos

`/rh` liga/desliga · `/rh teste` · `/rh som` · `/rh fonte 15` · `/rh escala 1.2` · `/rh altura 26` (distância acima
da nameplate) · `/rh eu 90` · `/rh blizz` · `/rh debug`

Precisa das nameplates de inimigos ligadas para o dano ficar acima do mob. Som só para o que você acerta: magias, tiros de varinha e cada tick de canalizada (Drain Life, Arcane Missiles, Blizzard); tick de DoT, pet e outros jogadores não tocam som.

## Arte e sons

Tudo feito do zero, sem arquivos do jogo: `py make_runehits_art.py` desenha os splats e a fonte dos números,
`py make_runehits_sounds.py` sintetiza os sons. Para trocar um som, coloque seu próprio `.ogg` em `sounds/` com o
mesmo nome. Teste: `py test_runehits.py` (precisa de `pip install lupa`).

Licença MIT (`LICENSE`). Projeto de fã, sem ligação com a Jagex ou a Blizzard.
