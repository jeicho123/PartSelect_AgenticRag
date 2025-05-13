-- Enable vector extension
create extension if not exists vector;

-- Create table to store embeddings + content
create table partselect_chunks (
    id uuid default gen_random_uuid() primary key,
    url text not null,
    content text not null,
    embedding vector(1536) not null
);

-- Create function to match chunks
create function match_partselect_chunks(
    query_embedding vector(1536),
    match_count int
)
returns table (
    url text,
    content text,
    similarity float
)
language plpgsql
as $$
begin
  return query
  select
    url,
    content,
    1 - (embedding <=> query_embedding) as similarity
  from partselect_chunks
  order by embedding <=> query_embedding
  limit match_count;
end;
$$;
