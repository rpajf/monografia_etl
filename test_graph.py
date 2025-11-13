# import time
# import matplotlib.pyplot as plt
# import seaborn as sns

# # Exemplo de função que queremos medir
# def processamento(n):
#     total = 0
#     for i in range(n):
#         total += i ** 2
#     return total

# # Testar tempos com diferentes tamanhos de entrada
# tamanhos = [1000, 5000, 10000, 20000, 50000]
# tempos = []

# for n in tamanhos:
#     inicio = time.perf_counter()
#     processamento(n)
#     fim = time.perf_counter()
#     tempos.append(fim - inicio)

# # Gráfico com matplotlib + seaborn
# sns.set(style="whitegrid")
# plt.figure(figsize=(8, 5))
# sns.lineplot(x=tamanhos, y=tempos, marker="o")
# plt.title("Desempenho da função processamento(n)")
# plt.xlabel("Tamanho da entrada (n)")
# plt.ylabel("Tempo de execução (segundos)")
# plt.show()

import time
import matplotlib.pyplot as plt
import seaborn as sns

def processamento(n):
    total = 0
    for i in range(n):
        total += i ** 2
    return total

tamanhos = [1000, 5000, 10000, 20000, 50000]
tempos = []

for n in tamanhos:
    inicio = time.perf_counter()
    processamento(n)
    fim = time.perf_counter()
    tempos.append(fim - inicio)

sns.set(style="whitegrid")
plt.figure(figsize=(8, 5))
sns.lineplot(x=tamanhos, y=tempos, marker="o")
plt.title("Desempenho da função processamento(n)")
plt.xlabel("Tamanho da entrada (n)")
plt.ylabel("Tempo de execução (segundos)")

plt.tight_layout()
plt.savefig("graph.png")
print("✅ Gráfico salvo como graph.png")