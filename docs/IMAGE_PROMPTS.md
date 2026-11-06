# Image prompts for ChatGPT

To make the images, paste the **style block** and then one **scene** into ChatGPT, save the result
under `docs/images/` with the filename shown. `README.md` already uses all five, so saving a new
version replaces the old one.

## Style block

```text
Create an image in the style of a retro 1960s space-age travel poster crossed with a modern
science magazine cover: bold flat shapes, grainy screen-print texture, a limited palette of deep
navy, warm gold, coral and cream, with dramatic light. The tone is deadpan and witty: treat
something ridiculous with complete seriousness. The spacecraft is a single vast, razor-thin square
mirror sail, held by four slender diagonal booms, with a tiny box-shaped payload at its centre.
Keep it tasteful and family-friendly, with no real logos, no real people and no extra text apart
from any words I specify. Spell any specified words exactly as given.
```

## Scenes

### 1. Hero banner: `hero.png` (wide, 16:9)

```text
A giant brass wind-up catapult bolted to a huge blazing Sun at lower left has just launched a tiny
golden solar sail towards two bright stars, one yellow and one orange, with a faint red dot beside
them at far upper right. An enormous gulf of empty star-speckled space fills the image between them.
At upper left, in a retro badge: "ASS". At lower right, in large type: "Alpha Centauri or bust.
Estimated arrival: year 9,247."
```

### 2. Travel poster: `travel-poster.png` (16:9)

```text
A vintage tourism poster for a rocky planet with a huge red dwarf star in its sky and elegant
stellar flares arcing overhead. A tiny solar sail glides in. At the top: "VISIT PROXIMA B". At the
bottom: "Only 4.25 light-years away. Flares included."
```

### 3. Mission control: `mission-control.png` (16:9)

```text
A 1960s mission control room with rows of consoles, staffed entirely by one small friendly robot
who is alone in the huge room and drinking coffee. The main wall display shows a progress bar at
0.000000% and the words "ALL TESTS PASSING". Through the window behind it, a calendar is falling
apart with age.
```

### 4. Sundiver: `sundiver.png` (16:9)

```text
A dramatic close-up of the mirror sail skimming the surface of the Sun, its edges glowing, with
huge solar prominences curling around it. A very small robot on the payload box holds up a tiny
parasol. Caption along the bottom: "Melting point: 933 K. Confidence: high."
```

### 5. Arrival: `arrival.png` (16:9)

```text
A battered, patched and ancient solar sail, covered in thousands of years of tiny impact holes,
finally reaches a quiet planet orbiting two golden suns. On the ground, a welcome party of
far-future humans who got there first by faster means are holding up a sign that reads: "WHAT TOOK
YOU SO LONG?"
```

## Tips

- If the lettering comes out wrong, ask for the image without text and add the words in an editor.
- If a filter objects to the acronym, write it as the letters "A.S.S." or leave it out of the image.
- Keep each file under about 1 MB so the README stays quick to load.
