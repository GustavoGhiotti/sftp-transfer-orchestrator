"""Entidade MapaArquivo — espelha 1 linha de TB_ARQUIVO_MAPA.

É a UNIDADE DE CONTROLE do orquestrador. Vínculo com a credencial por ID_CEDENTE.

Campos:
    id, id_cedente, descricao, origem, destino,
    padrao_arquivo, somente_hoje, renomear_com_data, ativo.

Sentido genérico SEM coluna de tipo: o protocolo é detectado pelo caminho
(SMB começa com '\\'; SFTP é qualquer outro), então o mesmo robô faz
SFTP->SMB, SMB->SFTP e SMB->SMB. O lado SFTP usa a credencial do cedente
(TB_CONEXAO_SFTP); o lado SMB usa o file server interno.

Regra implícita (não é coluna): se o arquivo baixado for .zip, o robô SEMPRE
extrai e grava apenas o conteúdo (1 arquivo interno, mesmo nome com outra
extensão); o .zip não é salvo. A única alteração possível no nome final é
acrescentar a data (renomear_com_data).
"""
