# Protótipo de Jogo de Plataforma 2D em Python

Este protótipo usa Pygame e traz uma base simples para evoluir um jogo estilo Mario Bros:

- personagem usando a imagem `dog_character.png`;
- gravidade e velocidade vertical;
- movimento horizontal;
- pulo apenas quando o personagem está no chão;
- colisão com plataformas;
- buracos entre partes do chão;
- plataformas em alturas diferentes;
- itens coletáveis;
- animações iniciais para `Parado`, `Andando`, `Abaixado`, `Parado olhando para cima`, `Latindo`, `Preparando salto`, `Pulando`, `Caindo`, `Amortecendo` e `Morrendo`;
- reinício com a tecla `R`.

## Como rodar

Instale o Pygame, se ainda não tiver:

```bash
pip install pygame
```

Depois execute:

```bash
python platformer_pygame.py
```

## Controles

- `A` ou seta esquerda: andar para a esquerda
- `D` ou seta direita: andar para a direita
- espaço: pular
- `W` ou seta para cima: olhar para cima quando estiver parado no chão
- `S` ou seta para baixo: abaixar
- `X`: latir
- `R`: reiniciar a fase

## Onde mexer primeiro

- Mude `platform_data` dentro de `build_level()` para redesenhar a fase.
- Mude `item_data` para reposicionar os itens.
- Ajuste `GRAVITY`, `MOVE_SPEED` e `JUMP_SPEED` para alterar a sensação do movimento.
- Troque `dog_character.png` para mudar o personagem.

## Como os sprites estão organizados

Os PNGs ficam em:

```text
jack_russell_sprites/
```

Arquivos atuais:

- `idle_0.png`: parado
- `walk_0.png` e `walk_1.png`: caminhada
- `crouch_0.png`: abaixado
- `look_up_0.png`: parado olhando para cima
- `bark_0.png` e `bark_1.png`: latindo
- `jump_prepare_0.png`: preparação do salto
- `jump_0.png`: subida do salto
- `fall_0.png`: queda
- `land_0.png` e `land_1.png`: pouso amortecido

## Como evoluir os movimentos

As animações ficam em `load_character_animations()`.

Cada estado aponta para uma lista de frames. Para deixar uma ação mais fluida, adicione novos PNGs na pasta e inclua os frames na lista:

```python
"walk": [
    sprite("walk_0.png"),
    sprite("walk_1.png"),
    sprite("walk_2.png"),
]
```

Os estados já estão preparados:

- `idle`: parado
- `walk`: andando
- `crouch`: abaixado
- `look_up`: parado olhando para cima
- `bark`: latindo
- `jump_prepare`: preparando salto
- `jump`: pulando
- `fall`: caindo
- `land`: amortecendo ao tocar o chão
- `dead`: morrendo

O método `choose_animation_state()` decide automaticamente qual movimento aparece de acordo com velocidade, chão, salto, queda e pouso.

O script `work/prepare_dog_sprites.py` registra o processo usado para preparar as imagens: ele remove o fundo, centraliza cada pose e salva os frames prontos para o jogo.
