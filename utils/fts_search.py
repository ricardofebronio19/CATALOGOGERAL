"""
Sistema de Full-Text Search com SQLite FTS5 para CGI
Implementa busca avançada por relevância com suporte a português
"""

import sqlite3
import os
from typing import List, Dict, Any, Optional
from flask import current_app
from app import db, get_logger
from models import Produto

logger = get_logger('fts')

class FullTextSearch:
    """Classe para gerenciar Full-Text Search com SQLite FTS5"""
    
    def __init__(self, db_path: str = None):
        if db_path:
            self.db_path = db_path
        else:
            try:
                self.db_path = current_app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            except RuntimeError:
                # Fallback quando não há contexto da aplicação
                from app import APP_DATA_PATH
                import os
                self.db_path = os.path.join(APP_DATA_PATH, 'catalogo.db')
        self.fts_table = 'produtos_fts'
        
    def _get_connection(self) -> sqlite3.Connection:
        """Obtém conexão direta com SQLite para operações FTS5"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Permite acesso por nome da coluna
        return conn

    def _get_existing_table_sql(self, conn: sqlite3.Connection) -> Optional[str]:
        """Retorna o SQL usado para criar a tabela FTS atual, se existir."""
        cursor = conn.execute(
            """
            SELECT sql
            FROM sqlite_master
            WHERE type='table' AND name=?;
            """,
            (self.fts_table,),
        )
        row = cursor.fetchone()
        return row["sql"] if row and row["sql"] else None

    def _uses_legacy_contentless_schema(self, table_sql: Optional[str]) -> bool:
        """Detecta o schema legado contentless que retorna colunas nulas nas leituras."""
        if not table_sql:
            return False
        normalized_sql = table_sql.lower().replace(' ', '')
        return "content=''" in normalized_sql or 'content=""' in normalized_sql
    
    def create_fts_table(self) -> bool:
        """Cria a tabela FTS5 se não existir"""
        try:
            with self._get_connection() as conn:
                # Verifica se a extensão FTS5 está disponível
                cursor = conn.execute("PRAGMA compile_options;")
                options = [row[0] for row in cursor.fetchall()]
                if not any('FTS5' in option for option in options):
                    logger.error("SQLite FTS5 não está disponível nesta instalação")
                    return False

                existing_table_sql = self._get_existing_table_sql(conn)
                if self._uses_legacy_contentless_schema(existing_table_sql):
                    logger.warning(
                        "Schema FTS legado detectado; recriando índice para restaurar leituras válidas"
                    )
                    conn.execute(f"DROP TABLE IF EXISTS {self.fts_table};")
                
                # Cria tabela FTS5
                create_sql = f"""
                CREATE VIRTUAL TABLE IF NOT EXISTS {self.fts_table} USING fts5(
                    produto_id UNINDEXED,
                    codigo,
                    nome,
                    fornecedor, 
                    grupos,
                    conversoes,
                    aplicacoes,
                    medidas,
                    observacoes,
                    tokenize='porter ascii'
                );
                """
                conn.execute(create_sql)
                
                # Cria trigger para manter sincronizado com a tabela principal
                trigger_sql = f"""
                CREATE TRIGGER IF NOT EXISTS produtos_fts_sync_insert 
                AFTER INSERT ON produto BEGIN
                    INSERT INTO {self.fts_table}(
                        produto_id, codigo, nome, fornecedor, grupos, 
                        conversoes, aplicacoes, medidas, observacoes
                    ) VALUES (
                        NEW.id, NEW.codigo, NEW.nome, NEW.fornecedor, NEW.grupo,
                        NEW.conversoes, '', NEW.medidas, NEW.observacoes
                    );
                END;
                """
                conn.execute(trigger_sql)
                
                trigger_update_sql = f"""
                CREATE TRIGGER IF NOT EXISTS produtos_fts_sync_update 
                AFTER UPDATE ON produto BEGIN
                    UPDATE {self.fts_table} SET
                        codigo = NEW.codigo,
                        nome = NEW.nome,
                        fornecedor = NEW.fornecedor,
                        grupos = NEW.grupo,
                        conversoes = NEW.conversoes,
                        medidas = NEW.medidas,
                        observacoes = NEW.observacoes
                    WHERE produto_id = NEW.id;
                END;
                """
                conn.execute(trigger_update_sql)
                
                trigger_delete_sql = f"""
                CREATE TRIGGER IF NOT EXISTS produtos_fts_sync_delete 
                AFTER DELETE ON produto BEGIN
                    DELETE FROM {self.fts_table} WHERE produto_id = OLD.id;
                END;
                """
                conn.execute(trigger_delete_sql)

                # Mantém o texto consolidado de aplicações sincronizado no FTS
                trigger_aplicacao_insert_sql = f"""
                CREATE TRIGGER IF NOT EXISTS produtos_fts_sync_aplicacao_insert
                AFTER INSERT ON aplicacao BEGIN
                    UPDATE {self.fts_table}
                    SET aplicacoes = (
                        SELECT GROUP_CONCAT(
                            COALESCE(a.montadora, '') || ' ' ||
                            COALESCE(a.veiculo, '') || ' ' ||
                            COALESCE(a.motor, '') || ' ' ||
                            COALESCE(a.ano, ''),
                            ' | '
                        )
                        FROM aplicacao a
                        WHERE a.produto_id = NEW.produto_id
                    )
                    WHERE produto_id = NEW.produto_id;
                END;
                """
                conn.execute(trigger_aplicacao_insert_sql)

                trigger_aplicacao_update_sql = f"""
                CREATE TRIGGER IF NOT EXISTS produtos_fts_sync_aplicacao_update
                AFTER UPDATE ON aplicacao BEGIN
                    UPDATE {self.fts_table}
                    SET aplicacoes = (
                        SELECT GROUP_CONCAT(
                            COALESCE(a.montadora, '') || ' ' ||
                            COALESCE(a.veiculo, '') || ' ' ||
                            COALESCE(a.motor, '') || ' ' ||
                            COALESCE(a.ano, ''),
                            ' | '
                        )
                        FROM aplicacao a
                        WHERE a.produto_id = NEW.produto_id
                    )
                    WHERE produto_id = NEW.produto_id;

                    UPDATE {self.fts_table}
                    SET aplicacoes = (
                        SELECT GROUP_CONCAT(
                            COALESCE(a.montadora, '') || ' ' ||
                            COALESCE(a.veiculo, '') || ' ' ||
                            COALESCE(a.motor, '') || ' ' ||
                            COALESCE(a.ano, ''),
                            ' | '
                        )
                        FROM aplicacao a
                        WHERE a.produto_id = OLD.produto_id
                    )
                    WHERE produto_id = OLD.produto_id;
                END;
                """
                conn.execute(trigger_aplicacao_update_sql)

                trigger_aplicacao_delete_sql = f"""
                CREATE TRIGGER IF NOT EXISTS produtos_fts_sync_aplicacao_delete
                AFTER DELETE ON aplicacao BEGIN
                    UPDATE {self.fts_table}
                    SET aplicacoes = (
                        SELECT GROUP_CONCAT(
                            COALESCE(a.montadora, '') || ' ' ||
                            COALESCE(a.veiculo, '') || ' ' ||
                            COALESCE(a.motor, '') || ' ' ||
                            COALESCE(a.ano, ''),
                            ' | '
                        )
                        FROM aplicacao a
                        WHERE a.produto_id = OLD.produto_id
                    )
                    WHERE produto_id = OLD.produto_id;
                END;
                """
                conn.execute(trigger_aplicacao_delete_sql)
                
                conn.commit()
                logger.info(f"Tabela FTS5 '{self.fts_table}' criada com sucesso")
                return True
                
        except Exception as e:
            logger.error(f"Erro ao criar tabela FTS5: {str(e)}")
            return False
    
    def populate_fts_table(self) -> bool:
        """Popula a tabela FTS5 com dados existentes"""
        try:
            with self._get_connection() as conn:
                # Limpa dados existentes
                conn.execute(f"DELETE FROM {self.fts_table};")
                
                # Insere todos os produtos existentes
                insert_sql = f"""
                INSERT INTO {self.fts_table}(
                    produto_id, codigo, nome, fornecedor, grupos, 
                    conversoes, aplicacoes, medidas, observacoes
                )
                SELECT 
                    p.id,
                    p.codigo,
                    p.nome,
                    p.fornecedor,
                    p.grupo,
                    p.conversoes,
                    GROUP_CONCAT(
                        a.montadora || ' ' || a.veiculo || ' ' || 
                        COALESCE(a.motor, '') || ' ' || COALESCE(a.ano, ''), ' | '
                    ) as aplicacoes,
                    p.medidas,
                    p.observacoes
                FROM produto p
                LEFT JOIN aplicacao a ON p.id = a.produto_id
                GROUP BY p.id, p.codigo, p.nome, p.fornecedor, p.grupo, 
                         p.conversoes, p.medidas, p.observacoes;
                """
                
                result = conn.execute(insert_sql)
                count = result.rowcount
                conn.commit()
                
                logger.info(f"Tabela FTS5 populada com {count} registros")
                return True
                
        except Exception as e:
            logger.error(f"Erro ao popular tabela FTS5: {str(e)}")
            return False
    
    def search(
        self,
        query: str,
        limit: int = 50,
        offset: int = 0,
        _allow_repair: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Realiza busca full-text e retorna resultados ordenados por relevância
        
        Args:
            query: Termo de busca
            limit: Número máximo de resultados
            offset: Offset para paginação
            
        Returns:
            Lista de dicionários com dados dos produtos encontrados
        """
        if not query or not query.strip():
            return []
        
        try:
            # Prepara query para FTS5 (remove caracteres especiais)
            clean_query = self._clean_fts_query(query.strip())
            if not clean_query:
                return []
            
            with self._get_connection() as conn:
                # Query FTS5 com ranking por relevância
                search_sql = f"""
                SELECT 
                    f.produto_id,
                    f.codigo,
                    f.nome,
                    f.fornecedor,
                    f.grupos,
                    f.conversoes,
                    f.aplicacoes,
                    f.medidas,
                    f.observacoes,
                    bm25({self.fts_table}) as relevancia
                FROM {self.fts_table} f
                WHERE {self.fts_table} MATCH ?
                ORDER BY bm25({self.fts_table})
                LIMIT ? OFFSET ?
                """
                
                cursor = conn.execute(search_sql, (clean_query, limit, offset))
                results = []
                
                for row in cursor.fetchall():
                    results.append({
                        'produto_id': row['produto_id'],
                        'codigo': row['codigo'],
                        'nome': row['nome'],
                        'fornecedor': row['fornecedor'],
                        'grupos': row['grupos'],
                        'conversoes': row['conversoes'],
                        'aplicacoes': row['aplicacoes'],
                        'medidas': row['medidas'],
                        'observacoes': row['observacoes'],
                        'relevancia': row['relevancia']
                    })

                if results and all(result['produto_id'] is None for result in results):
                    logger.warning(
                        "Busca FTS retornou registros sem produto_id; tentando reconstruir índice"
                    )
                    if _allow_repair and self.rebuild_index():
                        return self.search(query, limit=limit, offset=offset, _allow_repair=False)
                    return []
                
                logger.debug(f"Busca FTS5 '{query}' retornou {len(results)} resultados")
                return results
                
        except Exception as e:
            logger.error(f"Erro na busca FTS5: {str(e)}")
            return []
    
    def _clean_fts_query(self, query: str) -> str:
        """
        Limpa e prepara query para FTS5
        Remove caracteres especiais que podem causar erro de sintaxe
        """
        import re
        
        # Para códigos com pontos, tenta diferentes estratégias
        original_query = query.strip()
        
        # Se contém hífen ou barra, converte para espaços (FTS5 não funciona bem com esses separadores)
        if '-' in original_query or '/' in original_query:
            # Substitui hífen e barra por espaço para que FTS5 trate como múltiplos termos
            original_query = original_query.replace('-', ' ').replace('/', ' ')
            # Remove múltiplos espaços
            original_query = re.sub(r'\s+', ' ', original_query).strip()
        
        # Se contém pontos, tenta diferentes estratégias
        if '.' in original_query:
            # Versão com aspas para busca exata
            quoted_version = f'"{original_query}"'
            # Versão sem pontos para busca flexível  
            no_dots_version = original_query.replace('.', ' ')
            # Remove múltiplos espaços
            no_dots_version = re.sub(r'\s+', ' ', no_dots_version).strip()
            terms_no_dots = [term.strip() for term in no_dots_version.split() if term.strip()]
            
            if terms_no_dots:
                wildcard_terms = ' OR '.join([f'{term}*' for term in terms_no_dots])
                return f'{quoted_version} OR ({wildcard_terms})'
            else:
                return quoted_version
        
        # Para queries normais (sem pontos), usa lógica original
        # Remove caracteres especiais do FTS5, exceto pontos que já foram tratados
        query = re.sub(r'[^\w\s\*\-\+]', ' ', query)
        
        # Divide em termos individuais
        terms = [term.strip() for term in query.split() if term.strip()]
        
        if not terms:
            return ''
        
        # Para busca mais flexível, adiciona * ao final de cada termo.
        # Múltiplos termos usam AND para que o documento precise conter TODOS os
        # termos (ex: "homocinetica celta" não deve retornar todas as homociné-
        # ticas, apenas as compatíveis com Celta).
        if len(terms) == 1:
            return f'"{terms[0]}" OR {terms[0]}*'
        else:
            # Frase exata OU todos os termos presentes (AND entre wildcards)
            exact_phrase = '"' + ' '.join(terms) + '"'
            wildcard_terms = ' AND '.join([f'{term}*' for term in terms])
            return f'{exact_phrase} OR ({wildcard_terms})'
    
    def get_search_suggestions(self, query: str, limit: int = 5) -> List[str]:
        """
        Retorna sugestões de busca baseadas no termo parcial
        """
        if not query or len(query) < 2:
            return []
        
        try:
            with self._get_connection() as conn:
                # Busca termos similares em códigos e nomes
                suggestions_sql = f"""
                SELECT DISTINCT 
                    CASE 
                        WHEN codigo LIKE ? THEN codigo
                        WHEN nome LIKE ? THEN nome
                        ELSE fornecedor
                    END as sugestao
                FROM produto 
                WHERE 
                    codigo LIKE ? OR 
                    nome LIKE ? OR 
                    fornecedor LIKE ?
                ORDER BY 
                    LENGTH(sugestao),
                    sugestao
                LIMIT ?
                """
                
                pattern = f'%{query}%'
                cursor = conn.execute(suggestions_sql, 
                                    (pattern, pattern, pattern, pattern, pattern, limit))
                
                suggestions = [row['sugestao'] for row in cursor.fetchall() if row['sugestao']]
                return suggestions
                
        except Exception as e:
            logger.error(f"Erro ao buscar sugestões: {str(e)}")
            return []
    
    def rebuild_index(self) -> bool:
        """Reconstrói completamente o índice FTS5"""
        try:
            with self._get_connection() as conn:
                # Remove tabela existente
                conn.execute(f"DROP TABLE IF EXISTS {self.fts_table};")
                
                # Recria e popula
                if self.create_fts_table():
                    return self.populate_fts_table()
                
                return False
                
        except Exception as e:
            logger.error(f"Erro ao reconstruir índice FTS5: {str(e)}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas da tabela FTS5"""
        try:
            with self._get_connection() as conn:
                # Verifica se a tabela existe ANTES de consultar
                cursor = conn.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name=?;
                """, (self.fts_table,))
                
                exists = cursor.fetchone() is not None
                
                total = 0
                if exists:
                    cursor = conn.execute(f"SELECT COUNT(*) as total FROM {self.fts_table};")
                    total = cursor.fetchone()['total']
                
                return {
                    'exists': exists,
                    'total_records': total,
                    'table_name': self.fts_table
                }
                
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas FTS5: {str(e)}")
            return {'exists': False, 'total_records': 0, 'table_name': self.fts_table}

# Instância global (lazy loading)
_fts_manager = None

def get_fts_manager() -> FullTextSearch:
    """Obtém a instância global do FTS manager (lazy loading)"""
    global _fts_manager
    if _fts_manager is None:
        _fts_manager = FullTextSearch()
    return _fts_manager

def init_fts(app):
    """Inicializa o sistema FTS5 com a aplicação Flask"""
    with app.app_context():
        try:
            fts_manager = get_fts_manager()
            if fts_manager.create_fts_table():
                # Verifica se precisamos popular a tabela
                stats = fts_manager.get_stats()
                if stats['exists'] and stats['total_records'] == 0:
                    fts_manager.populate_fts_table()
                    logger.info("Sistema FTS5 inicializado com sucesso")
                return True
        except Exception as e:
            logger.error(f"Erro ao inicializar FTS5: {str(e)}")
    
    return False