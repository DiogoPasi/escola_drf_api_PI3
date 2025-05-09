from django.db import models

class Administracao(models.Model):
    """Modelo para funcionários administrativos da escola."""
    nome = models.CharField(max_length=255)
    cpf = models.CharField(max_length=14, unique=True) # Assumindo formato padrão de CPF
    email = models.EmailField(unique=True)
    celular = models.CharField(max_length=20, blank=False, null=False) # Campo obrigatório

    def __str__(self):
        return self.nome

class Professores(models.Model):
    """Modelo para professores."""
    nome = models.CharField(max_length=255)
    cpf = models.CharField(max_length=14, unique=True)
    email = models.EmailField(unique=True)
    celular = models.CharField(max_length=20, blank=False, null=False) # Campo obrigatório

    def __str__(self):
        return self.nome

class Responsaveis(models.Model):
    """Modelo para responsáveis de alunos."""
    nome = models.CharField(max_length=255)
    cpf = models.CharField(max_length=14, unique=True)
    email = models.EmailField(unique=True, blank=False, null=False) # Campo obrigatório
    celular = models.CharField(max_length=20, blank=False, null=False) # Campo obrigatório

    def __str__(self):
        return self.nome

class Alunos(models.Model):
    """Modelo para alunos."""
    nome = models.CharField(max_length=255)
    rg = models.CharField(max_length=20, unique=True) # Assumindo RG é único
    data_de_nascimento = models.DateField()
    email = models.EmailField(unique=True, blank=True, null=True) # Campo opcional
    celular = models.CharField(max_length=20, blank=True, null=True) # Campo opcional
    ra = models.CharField(max_length=50, unique=True) # Registro Acadêmico (RA) do aluno

    # Um aluno pode ter vários responsáveis, e um responsável pode ter vários alunos
    responsaveis = models.ManyToManyField(Responsaveis, related_name='alunos')

    def __str__(self):
        return f"{self.nome} ({self.ra})"

class Materias(models.Model):
    """Modelo para matérias de estudo (ex: Matemática, História)."""
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True, null=True) # Campo opcional

    def __str__(self):
        return self.nome

class Classes(models.Model):
    """Modelo para turmas ou classes de alunos."""
    nome = models.CharField(max_length=255, unique=True)
    ano_letivo = models.IntegerField() # Usando IntegerField para o ano letivo

    # Uma turma pode ter muitos alunos, e um aluno pode estar em muitas turmas
    alunos = models.ManyToManyField(Alunos, related_name='classes')

    # Uma turma pode ter muitos professores, e um professor pode lecionar em muitas turmas
    professores = models.ManyToManyField(Professores, related_name='classes')

    # Uma turma estuda muitas matérias, e uma matéria pode ser estudada por muitas turmas
    materias = models.ManyToManyField(Materias, related_name='classes')

    def __str__(self):
        return self.nome

class Avaliacoes(models.Model):
    """Modelo para tipos de avaliações (ex: 'Prova', 'Trabalho', 'Participação')."""
    nome = models.CharField(max_length=255, unique=True) # Assumindo nomes de avaliações são únicos globalmente
    descricao = models.TextField(blank=True, null=True) # Campo opcional
    #Professor responsável
    professor_responsavel = models.ForeignKey(Professores, on_delete=models.SET_NULL, null=True, blank=True, related_name='avaliacoes_criadas') # Se o professor for deletado, set to NULL

    def __str__(self):
        return self.nome

class Notas(models.Model):
    """Modelo para armazenar a nota de um aluno para uma avaliação específica, vinculada a um professor."""
    # Armazenar nota como Decimal para precisão
    nota = models.DecimalField(max_digits=5, decimal_places=2)

    # Uma nota é para um aluno específico
    aluno = models.ForeignKey(Alunos, on_delete=models.CASCADE, related_name='notas')

    # Uma nota é para uma avaliação específica
    avaliacao = models.ForeignKey(Avaliacoes, on_delete=models.CASCADE, related_name='notas')

    # Uma nota é tipicamente atribuída por um professor (link opcional)
    atribuida_por = models.ForeignKey(Professores, on_delete=models.SET_NULL, null=True, blank=True, related_name='notas_atribuidas')

    # Adicionar um campo de data para quando a nota foi registrada
    data_registro = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Nota de {self.aluno.nome} para {self.avaliacao.nome}: {self.nota}"

    class Meta:
        # Opcional: Adicionar uma restrição para evitar notas duplicadas para o mesmo aluno/avaliação
        # Dependendo dos requisitos, você pode permitir várias notas para a mesma avaliação (ex: recuperações)
        # Adicionar unique_together para aluno e avaliacao é comum se apenas uma nota por avaliação for permitida
        unique_together = ('aluno', 'avaliacao')
        pass