-- Feature 4 (coordenação entre grupos): novos campos do Grupo na tabela grupos.
-- Idempotente: seguro rodar mais de uma vez.
-- Rodar manualmente no editor SQL do Supabase.

alter table grupos
    add column if not exists regiao text not null default '';

alter table grupos
    add column if not exists pedido_ajuda boolean not null default false;
