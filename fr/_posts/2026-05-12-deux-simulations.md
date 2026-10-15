---
title: Deux simulations valent-elles mieux qu’une ?
date: 2026-05-12
ref: two-simulations
summary: Une intuition séduisante sur les maillages, une petite expérience en 1D, et la leçon qu’elle m’a donnée sur la différence entre information et précision.
image: /assets/images/blog/two-simulations.webp
image_alt: Croquis à l’encre bleue d’une courbe approchée par deux maillages décalés, l’un en points pleins, l’autre en cercles terre cuite.
image_caption: Deux maillages qui ne se touchent jamais, une seule solution à approcher.
published: true
---

Il y a quelques mois, une idée m’a tenu éveillé plus longtemps que prévu. Elle avait tout pour plaire : simple, élégante, et légèrement subversive vis-à-vis de ce qu’on apprend en analyse numérique.

## Les lois physiques se moquent de la forme

Quand on écrit la loi de Faraday sur une face, elle reste vraie quelle que soit la forme de cette face : carrée, tordue, triangulaire. Elle ne dépend que de son bord, et même la connectivité de ce bord importe peu. C’est ce qu’on appelle une loi *topologique*.

Si on prend cette remarque au sérieux, on peut voir les grandeurs physiques comme des choses que l’on évalue sur des entités géométriques : des sommets, des arêtes, des faces, des cellules. Un maillage n’est alors qu’un choix particulier d’entités, un peu comme on choisirait où placer des capteurs dans un laboratoire.

## L’intuition

Dans un laboratoire, si je double le nombre de capteurs sans jamais en placer deux au même endroit, je double l’information dont je dispose sur le champ que je mesure.

Alors pourquoi ne pas faire pareil en simulation ? Deux maillages qui ne coïncident nulle part, deux simulations indépendantes, et le champ connu « deux fois mieux ». Pourtant, la théorie classique est formelle : l’erreur se mesure avec le pas du maillage, noté *h*, et deux simulations au même pas restent en *O(h)*. Rien ne gagne, sur le papier.

L’une des deux visions devait se tromper. J’espérais secrètement que ce soit la théorie classique.

## L’expérience

Plutôt que de théoriser pendant des semaines, j’ai pris le cas le plus simple possible : l’équation *−u″ = f* sur un segment. Deux maillages décalés, deux solutions approchées, puis une forme qui coïncide avec chacune sur ses propres points.

Résultat : au milieu du segment, le schéma tombe juste. Mais dès que je déplace le point de calcul, la valeur ne bouge pas comme elle devrait. La loi physique est bien respectée sur chacun des deux maillages… et pourtant la combinaison des deux ne s’approche pas mieux de la solution exacte qu’un seul maillage plus fin.

> J’avais bien deux mesures indépendantes. Je n’avais pas deux fois moins d’erreur.

## Où était l’erreur ?

Il m’a fallu un moment pour la voir. La partie topologique du modèle, celle qui dit comment les grandeurs se relient, est exacte. Mais un schéma numérique a aussi besoin d’une partie *métrique* : des longueurs, des aires, la façon dont le milieu relie un flux à une circulation. C’est là que naît l’erreur.

Et cette erreur-là n’a rien à voir avec le nombre d’entités que l’on utilise. Elle dépend de la forme des cellules. Ajouter un second maillage ajoute de l’information topologique, mais ne corrige pas la métrique de chacun.

J’aime bien la formuler ainsi : la topologie dit quels chemins sont possibles, la métrique dit comment on les parcourt. Multiplier les chemins ne rend pas le pas plus juste.

## Ce que j’en retiens

- **Information n’est pas précision.** Deux jeux de données ne se combinent bien que si l’on sait d’où vient l’erreur de chacun.
- **Une petite expérience vaut mieux qu’une longue théorie.** Le cas 1D a mis mon intuition à l’épreuve en un après-midi.
- **Une idée fausse peut être féconde.** Elle m’a obligé à séparer clairement ce qui, dans un schéma, relève de la structure et ce qui relève de la mesure.

La question reste ouverte, d’ailleurs : existe-t-il des métriques pour lesquelles deux simulations valent vraiment mieux qu’une ? Je n’en sais rien. Mais je sais maintenant où chercher.
