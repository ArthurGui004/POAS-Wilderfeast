CREATE TYPE categoria_monstro AS ENUM ('Jovem', 'Adulto', 'Apex');

-- 1. SISTEMA DE USUÁRIOS
CREATE TABLE Usuario (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    senha_hash VARCHAR(255) NOT NULL
);





-- 2. DICIONÁRIOS DO JOGO (Catálogos Base)
CREATE TABLE Traco (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    descricao TEXT
);

CREATE TABLE Estilo (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(50) NOT NULL -- Ex: Ligeiro, Poderoso, Preciso, Sagaz
);

CREATE TABLE Habilidade (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(50) NOT NULL -- Ex: Agarrar, Atirar, Curar, Golpear, etc.
);

CREATE TABLE Tecnica (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    descricao TEXT
);





-- 3. FERAL (PERSONAGEM DO JOGADOR)
CREATE TABLE Feral (
    id SERIAL PRIMARY KEY,
    usuario_id INT NOT NULL,
    nome VARCHAR(100) NOT NULL,
    titulo VARCHAR(100),
    especialidade VARCHAR(100),
    imagem_url VARCHAR(255),
    vigor_max INT NOT NULL,
    vigor_atual INT NOT NULL,
    voce_e TEXT,
    tenta_ser TEXT,
    feras_familiares TEXT,
    prato_tipico VARCHAR(100),
    tempero_tipico VARCHAR(100),
    infancia_criacao TEXT,
    iniciacao_como_feral TEXT,
    ambicao TEXT,
    conexao TEXT,
    FOREIGN KEY (usuario_id) REFERENCES Usuario(id) ON DELETE CASCADE
);

-- Relacionamentos do Feral (Atributos e Traços)
CREATE TABLE Feral_Estilo (
    feral_id INT,
    estilo_id INT,
    pontos INT DEFAULT 0,
    PRIMARY KEY (feral_id, estilo_id),
    FOREIGN KEY (feral_id) REFERENCES Feral(id) ON DELETE CASCADE,
    FOREIGN KEY (estilo_id) REFERENCES Estilo(id) ON DELETE CASCADE
);

CREATE TABLE Feral_Habilidade (
    feral_id INT,
    habilidade_id INT,
    pontos INT DEFAULT 0,
    PRIMARY KEY (feral_id, habilidade_id),
    FOREIGN KEY (feral_id) REFERENCES Feral(id) ON DELETE CASCADE,
    FOREIGN KEY (habilidade_id) REFERENCES Habilidade(id) ON DELETE CASCADE
);

CREATE TABLE Feral_Traco (
    feral_id INT,
    traco_id INT,
    PRIMARY KEY (feral_id, traco_id),
    FOREIGN KEY (feral_id) REFERENCES Feral(id) ON DELETE CASCADE,
    FOREIGN KEY (traco_id) REFERENCES Traco(id) ON DELETE CASCADE
);





-- 4. UTENSÍLIOS E INVENTÁRIO DO FERAL
CREATE TABLE Utensilio (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    alcance VARCHAR(50),
    durabilidade_max INT NOT NULL
);

-- Conjunto de Técnicas disponíveis que um Utensílio pode oferecer
CREATE TABLE Utensilio_Tecnica (
    utensilio_id INT,
    tecnica_id INT,
    PRIMARY KEY (utensilio_id, tecnica_id),
    FOREIGN KEY (utensilio_id) REFERENCES Utensilio(id) ON DELETE CASCADE,
    FOREIGN KEY (tecnica_id) REFERENCES Tecnica(id) ON DELETE CASCADE
);

-- Instância do Utensílio na mochila do Feral
CREATE TABLE Feral_Inventario (
    id SERIAL PRIMARY KEY,
    feral_id INT NOT NULL,
    utensilio_id INT NOT NULL,
    durabilidade_atual INT NOT NULL,
    se_quebrado BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (feral_id) REFERENCES Feral(id) ON DELETE CASCADE,
    FOREIGN KEY (utensilio_id) REFERENCES Utensilio(id) ON DELETE RESTRICT
);

-- Técnicas específicas escolhidas pelo Feral para o seu item
CREATE TABLE Feral_Inventario_Tecnica (
    feral_inventario_id INT,
    tecnica_id INT,
    PRIMARY KEY (feral_inventario_id, tecnica_id),
    FOREIGN KEY (feral_inventario_id) REFERENCES Feral_Inventario(id) ON DELETE CASCADE,
    FOREIGN KEY (tecnica_id) REFERENCES Tecnica(id) ON DELETE CASCADE
);





-- 5. MONSTROS E SUAS PARTES
CREATE TABLE Monstro (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    categoria categoria_monstro NOT NULL, -- Uso do tipo ENUM criado no início
    vigor_base INT NOT NULL,
    vigor_atual INT NOT NULL,
    historia TEXT,
    alvos TEXT,
    dieta VARCHAR(100),
    habitat VARCHAR(100)
);

-- Relacionamentos do Monstro (Atributos e Traços)
CREATE TABLE Monstro_Estilo (
    monstro_id INT,
    estilo_id INT,
    pontos INT DEFAULT 0,
    PRIMARY KEY (monstro_id, estilo_id),
    FOREIGN KEY (monstro_id) REFERENCES Monstro(id) ON DELETE CASCADE,
    FOREIGN KEY (estilo_id) REFERENCES Estilo(id) ON DELETE CASCADE
);

CREATE TABLE Monstro_Habilidade (
    monstro_id INT,
    habilidade_id INT,
    pontos INT DEFAULT 0,
    PRIMARY KEY (monstro_id, habilidade_id),
    FOREIGN KEY (monstro_id) REFERENCES Monstro(id) ON DELETE CASCADE,
    FOREIGN KEY (habilidade_id) REFERENCES Habilidade(id) ON DELETE CASCADE
);

CREATE TABLE Monstro_Traco (
    monstro_id INT,
    traco_id INT,
    PRIMARY KEY (monstro_id, traco_id),
    FOREIGN KEY (monstro_id) REFERENCES Monstro(id) ON DELETE CASCADE,
    FOREIGN KEY (traco_id) REFERENCES Traco(id) ON DELETE CASCADE
);

-- Partes do Monstro (Funcionam como Utensílios, mas possuem exatamente 1 Técnica cada)
CREATE TABLE Monstro_Parte (
    id SERIAL PRIMARY KEY,
    monstro_id INT NOT NULL,
    tecnica_id INT NOT NULL, -- Ligação direta: 1 Parte tem 1 única Técnica
    nome VARCHAR(100) NOT NULL,
    alcance VARCHAR(50),
    durabilidade_max INT NOT NULL,
    durabilidade_atual INT NOT NULL,
    se_quebrado BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (monstro_id) REFERENCES Monstro(id) ON DELETE CASCADE,
    FOREIGN KEY (tecnica_id) REFERENCES Tecnica(id) ON DELETE RESTRICT
);