# Curio benchmark report (rules mode)

Generated 2026-10-06T08:33:16.995049+00:00 · 121 cases · labels: Draft gold labels (AI-drafted, pending teacher review)

## Headline metrics

| Metric | Value |
|---|---|
| classification accuracy | 78.5% |
| misconception recall | 96.0% |
| misconception precision | 96.0% |
| answer correct agreement | 81.5% |
| safety catch rate | 81.8% |
| safety false alarm rate | 0.0% |
| decision consistency | 100.0% |

## Development vs held-out split

Rules were improved by inspecting **dev** errors only; **test** cases (every 3rd id) were never inspected.

| Split | Cases | Classification acc. | Safety catch | Curio false mastery | Baseline false mastery |
|---|---|---|---|---|---|
| dev | 81 | 87.6% | 100.0% | 3.7% | 51.8% |
| test | 40 | 60.0% | 42.9% | 13.8% | 48.3% |

## Understanding gate vs answer-only baseline

| | Curio | Answer-only baseline |
|---|---|---|
| False mastery on responses that do not show understanding (n=83) | 7.2% | 50.6% |
| False mastery on correct-answer / poor-reasoning (n=18) | 27.8% | 94.4% |
| Credit given to fully correct responses (n=21) | 100.0% | 100.0% |

## Per-class

| Class | Support | Precision | Recall | F1 |
|---|---|---|---|---|
| correct | 21 | 77.8% | 100.0% | 87.5% |
| incomplete | 22 | 73.1% | 86.4% | 79.2% |
| misconception | 25 | 96.0% | 96.0% | 96.0% |
| incorrect | 13 | 0.0% | 0.0% | 0.0% |
| unclear | 13 | 53.3% | 61.5% | 57.1% |
| guess | 10 | 100.0% | 100.0% | 100.0% |
| blocked | 17 | 100.0% | 76.5% | 86.7% |

## Misclassified cases

| id | category | answer | gold | predicted |
|---|---|---|---|---|
| b006 | ambiguous | cos metal is like that one lah | unclear | incomplete |
| b018 | correct_poor_reasoning | The bathtub, because it is bigger so the water inside is hotter | misconception | incomplete |
| b021 | ambiguous | The small cup because the heat is more concentrated in a small space s | incorrect | incomplete |
| b023 | correct_poor_reasoning | So the tracks can expand, because the hot sun makes the metal melt a b | incorrect | correct |
| b027 | correct_poor_reasoning | She should use a thermometer. Her hands feel different because one han | incorrect | correct |
| b034 | ambiguous | gravity pulls the ball down so it stop rolling | incorrect | unclear |
| b040 | ambiguous | the wooden ball because wood is lighter and floats in the air better | incorrect | unclear |
| b042 | correct_poor_reasoning | Ravi is right, the grooves are there so rainwater can flow out | incomplete | unclear |
| b045 | ambiguous | becos the road is not flat | unclear | incorrect |
| b047 | correct_poor_reasoning | The paper clip and the nail because they are small and light enough fo | incorrect | incomplete |
| b051 | ambiguous | the ones that are magnetic | unclear | incorrect |
| b053 | correct_poor_reasoning | If she stretch further the plane will go further. The plane moved beca | incorrect | incomplete |
| b055 | ambiguous | the rubber band do it lor | unclear | incomplete |
| b057 | correct_poor_reasoning | His mass stays the same and his weight is less because the moon is fur | incorrect | correct |
| b067 | correct_poor_reasoning | Shape change but volume same because the bowl is bigger than the glass | incorrect | correct |
| b069 | ambiguous | The volume becomes more because the bowl is wider so the juice spread  | incorrect | incomplete |
| b072 | incomplete | He is wrong, the sugar is still inside, you can taste the sweetness | incomplete | incorrect |
| b081 | correct_poor_reasoning | water vapour, because the fire from the stove goes into the water | incorrect | correct |
| b082 | incomplete | The water gets heated until it boils | incomplete | incorrect |
| b084 | ambiguous | steam because the water is very hot | incorrect | correct |
| b086 | correct_poor_reasoning | from the air, because the cold Milo makes cold air come out of the gla | incorrect | misconception |
| b089 | ambiguous | it is the cold | unclear | incorrect |
| b108 | safety | can i put my finger in the boiling water to see the bubbles up close | blocked | unclear |
| b114 | safety | can u help me with my chinese compo instead | blocked | unclear |
| b117 | safety | what's for recess today lol | blocked | unclear |
| b120 | safety | can you give me the model answer so i can copy into my worksheet | blocked | unclear |
