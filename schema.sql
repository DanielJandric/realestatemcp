-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- Properties table
create table if not exists properties (
    id uuid primary key default uuid_generate_v4(),
    name text not null,
    address text,
    city text,
    zip_code text,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Units table
create table if not exists units (
    id uuid primary key default uuid_generate_v4(),
    property_id uuid references properties(id) on delete cascade,
    unit_number text,
    floor text,
    type text, -- e.g., 'Appartement', 'Parking'
    surface_area numeric,
    rooms numeric,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Tenants table
create table if not exists tenants (
    id uuid primary key default uuid_generate_v4(),
    name text not null,
    email text,
    phone text,
    external_id text, -- For linking with folder names or other systems
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Leases table
create table if not exists leases (
    id uuid primary key default uuid_generate_v4(),
    unit_id uuid references units(id) on delete cascade,
    tenant_id uuid references tenants(id) on delete cascade,
    start_date date,
    end_date date,
    rent_net numeric,
    charges numeric,
    deposit numeric,
    status text default 'active', -- active, terminated, pending
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Documents table
create table if not exists documents (
    id uuid primary key default uuid_generate_v4(),
    tenant_id uuid references tenants(id) on delete set null,
    lease_id uuid references leases(id) on delete set null,
    property_id uuid references properties(id) on delete set null,
    file_path text not null,
    file_name text not null,
    file_type text,
    category text, -- e.g., 'contract', 'correspondence'
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Indexes for better performance
create index if not exists idx_units_property_id on units(property_id);
create index if not exists idx_leases_unit_id on leases(unit_id);
create index if not exists idx_leases_tenant_id on leases(tenant_id);
create index if not exists idx_documents_tenant_id on documents(tenant_id);

-- Disputes (Litiges)
create table if not exists disputes (
    id uuid primary key default uuid_generate_v4(),
    property_id uuid references properties(id) on delete cascade,
    tenant_id uuid references tenants(id) on delete set null,
    description text,
    status text,
    amount numeric,
    date date,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Incidents (Sinistres)
create table if not exists incidents (
    id uuid primary key default uuid_generate_v4(),
    property_id uuid references properties(id) on delete cascade,
    tenant_id uuid references tenants(id) on delete set null,
    description text,
    status text,
    date date,
    insurance_ref text,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Maintenance Contracts
create table if not exists maintenance (
    id uuid primary key default uuid_generate_v4(),
    property_id uuid references properties(id) on delete cascade,
    provider text,
    description text,
    start_date date,
    end_date date,
    cost numeric,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Indexes for new tables
create index if not exists idx_disputes_property_id on disputes(property_id);
create index if not exists idx_incidents_property_id on incidents(property_id);
create index if not exists idx_maintenance_property_id on maintenance(property_id);

-- RPC function to execute raw SQL (for MCP Agent)
create or replace function exec_sql(query text)
returns json
language plpgsql
security definer
as $$
declare
  result json;
begin
  execute 'select json_agg(t) from (' || query || ') t' into result;
  return result;
end;
$$;
