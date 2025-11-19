-- Enhanced Schema with Constraints, Indexes, and Materialized Views
-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- ==================== TABLES ====================

-- Properties table
create table if not exists properties (
    id uuid primary key default uuid_generate_v4(),
    name text not null,
    address text,
    city text,
    zip_code text,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    
    -- Constraints
    constraint name_not_empty check (length(trim(name)) > 0)
);

-- Units table
create table if not exists units (
    id uuid primary key default uuid_generate_v4(),
    property_id uuid references properties(id) on delete cascade,
    unit_number text,
    floor text,
    type text,
    surface_area numeric,
    rooms numeric,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    
    -- Constraints
    constraint surface_area_positive check (surface_area is null or surface_area > 0),
    constraint rooms_positive check (rooms is null or rooms > 0)
);

-- Tenants table
create table if not exists tenants (
    id uuid primary key default uuid_generate_v4(),
    name text not null,
    email text,
    phone text,
    external_id text,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    
    -- Constraints
    constraint name_not_empty check (length(trim(name)) > 0),
    constraint email_format check (email is null or email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
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
    status text default 'active',
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    
    -- Constraints
    constraint rent_non_negative check (rent_net is null or rent_net >= 0),
    constraint charges_non_negative check (charges is null or charges >= 0),
    constraint deposit_non_negative check (deposit is null or deposit >= 0),
    constraint dates_logical check (end_date is null or start_date is null or end_date >= start_date),
    constraint valid_status check (status in ('active', 'terminated', 'pending', 'draft'))
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
    category text,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    
    -- Constraints
    constraint file_path_not_empty check (length(trim(file_path)) > 0),
    constraint file_name_not_empty check (length(trim(file_name)) > 0)
);

-- Disputes table
create table if not exists disputes (
    id uuid primary key default uuid_generate_v4(),
    property_id uuid references properties(id) on delete cascade,
    tenant_id uuid references tenants(id) on delete set null,
    description text,
    status text,
    amount numeric,
    date date,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    
    -- Constraints
    constraint amount_non_negative check (amount is null or amount >= 0),
    constraint valid_dispute_status check (status is null or status in ('open', 'in_progress', 'resolved', 'closed', 'pending'))
);

-- Incidents table
create table if not exists incidents (
    id uuid primary key default uuid_generate_v4(),
    property_id uuid references properties(id) on delete cascade,
    tenant_id uuid references tenants(id) on delete set null,
    description text,
    status text,
    date date,
    insurance_ref text,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    
    -- Constraints
    constraint valid_incident_status check (status is null or status in ('reported', 'investigating', 'resolved', 'closed', 'insurance_claim'))
);

-- Maintenance table
create table if not exists maintenance (
    id uuid primary key default uuid_generate_v4(),
    property_id uuid references properties(id) on delete cascade,
    provider text,
    description text,
    start_date date,
    end_date date,
    cost numeric,
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    
    -- Constraints
    constraint cost_non_negative check (cost is null or cost >= 0),
    constraint maintenance_dates_logical check (end_date is null or start_date is null or end_date >= start_date)
);

-- Audit log table for tracking changes
create table if not exists audit_log (
    id uuid primary key default uuid_generate_v4(),
    table_name text not null,
    record_id uuid not null,
    action text not null,
    old_data jsonb,
    new_data jsonb,
    changed_by text,
    changed_at timestamp with time zone default timezone('utc'::text, now()) not null,
    
    constraint valid_action check (action in ('INSERT', 'UPDATE', 'DELETE'))
);

-- ==================== INDEXES ====================

-- Existing indexes
create index if not exists idx_units_property_id on units(property_id);
create index if not exists idx_leases_unit_id on leases(unit_id);
create index if not exists idx_leases_tenant_id on leases(tenant_id);
create index if not exists idx_documents_tenant_id on documents(tenant_id);
create index if not exists idx_disputes_property_id on disputes(property_id);
create index if not exists idx_incidents_property_id on incidents(property_id);
create index if not exists idx_maintenance_property_id on maintenance(property_id);

-- New composite indexes for complex queries
create index if not exists idx_leases_unit_status on leases(unit_id, status);
create index if not exists idx_leases_tenant_status on leases(tenant_id, status);
create index if not exists idx_leases_dates on leases(start_date, end_date);
create index if not exists idx_disputes_property_status on disputes(property_id, status);
create index if not exists idx_incidents_property_status on incidents(property_id, status);
create index if not exists idx_maintenance_property_dates on maintenance(property_id, start_date, end_date);
create index if not exists idx_documents_category on documents(category);
create index if not exists idx_audit_log_table_record on audit_log(table_name, record_id);

-- Enable pg_trgm extension for text search (trigram indexes)
create extension if not exists pg_trgm;

-- Performance indexes for text search
create index if not exists idx_tenants_name_trgm on tenants using gin(name gin_trgm_ops);
create index if not exists idx_properties_name_trgm on properties using gin(name gin_trgm_ops);

-- ==================== MATERIALIZED VIEWS ====================

-- Portfolio summary view
create materialized view if not exists mv_portfolio_summary as
select 
    count(distinct p.id) as total_properties,
    count(distinct u.id) as total_units,
    count(distinct l.id) as total_leases,
    count(distinct t.id) as total_tenants,
    round(count(distinct l.id)::numeric / nullif(count(distinct u.id), 0) * 100, 2) as occupancy_rate,
    sum(l.rent_net) as total_rent_revenue,
    sum(l.charges) as total_charges_revenue,
    sum(l.rent_net + coalesce(l.charges, 0)) as total_monthly_revenue,
    sum(l.deposit) as total_deposits_held
from properties p
left join units u on u.property_id = p.id
left join leases l on l.unit_id = u.id and l.status = 'active'
left join tenants t on t.id = l.tenant_id;

create unique index on mv_portfolio_summary ((true));

-- Property-level occupancy and revenue
create materialized view if not exists mv_property_metrics as
select 
    p.id as property_id,
    p.name as property_name,
    p.city,
    count(distinct u.id) as unit_count,
    count(distinct case when l.status = 'active' then l.id end) as occupied_units,
    round(count(distinct case when l.status = 'active' then l.id end)::numeric / nullif(count(distinct u.id), 0) * 100, 2) as occupancy_rate,
    sum(case when l.status = 'active' then l.rent_net else 0 end) as monthly_rent,
    sum(case when l.status = 'active' then coalesce(l.charges, 0) else 0 end) as monthly_charges,
    sum(case when l.status = 'active' then l.rent_net + coalesce(l.charges, 0) else 0 end) as monthly_revenue,
    avg(case when l.status = 'active' and u.surface_area > 0 then l.rent_net / u.surface_area end) as avg_rent_per_sqm,
    count(distinct d.id) as active_disputes_count,
    sum(d.amount) as disputes_total_amount,
    count(distinct i.id) as incidents_count
from properties p
left join units u on u.property_id = p.id
left join leases l on l.unit_id = u.id
left join disputes d on d.property_id = p.id and d.status in ('open', 'in_progress')
left join incidents i on i.property_id = p.id and i.status not in ('closed', 'resolved')
group by p.id, p.name, p.city;

create unique index on mv_property_metrics (property_id);

-- Unit type analysis
create materialized view if not exists mv_unit_type_analysis as
select 
    u.type,
    count(distinct u.id) as unit_count,
    count(distinct l.id) as leased_count,
    round(count(distinct l.id)::numeric / nullif(count(distinct u.id), 0) * 100, 2) as occupancy_rate,
    avg(u.surface_area) as avg_surface_area,
    avg(u.rooms) as avg_rooms,
    avg(l.rent_net) as avg_rent,
    avg(case when u.surface_area > 0 then l.rent_net / u.surface_area end) as avg_rent_per_sqm,
    min(l.rent_net) as min_rent,
    max(l.rent_net) as max_rent
from units u
left join leases l on l.unit_id = u.id and l.status = 'active'
where u.type is not null
group by u.type;

create unique index on mv_unit_type_analysis (type);

-- ==================== FUNCTIONS ====================

-- Calculate occupancy rate for a property
create or replace function calculate_occupancy_rate(p_property_id uuid)
returns numeric
language plpgsql
as $$
declare
    v_total_units integer;
    v_occupied_units integer;
begin
    select count(*) into v_total_units
    from units where property_id = p_property_id;
    
    select count(distinct l.id) into v_occupied_units
    from leases l
    join units u on u.id = l.unit_id
    where u.property_id = p_property_id and l.status = 'active';
    
    if v_total_units = 0 then
        return 0;
    end if;
    
    return round((v_occupied_units::numeric / v_total_units) * 100, 2);
end;
$$;

-- Get rent trend for a property over time
create or replace function get_rent_trend(p_property_id uuid, p_months integer default 12)
returns table(month date, avg_rent numeric, lease_count bigint)
language plpgsql
as $$
begin
    return query
    select 
        date_trunc('month', l.start_date)::date as month,
        avg(l.rent_net) as avg_rent,
        count(*) as lease_count
    from leases l
    join units u on u.id = l.unit_id
    where u.property_id = p_property_id
        and l.start_date >= current_date - (p_months || ' months')::interval
    group by date_trunc('month', l.start_date)
    order by month desc;
end;
$$;

-- Refresh all materialized views
create or replace function refresh_all_materialized_views()
returns void
language plpgsql
as $$
begin
    refresh materialized view concurrently mv_portfolio_summary;
    refresh materialized view concurrently mv_property_metrics;
    refresh materialized view concurrently mv_unit_type_analysis;
end;
$$;

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

-- ==================== TRIGGERS ====================

-- Generic audit trigger function
create or replace function audit_trigger_func()
returns trigger
language plpgsql
as $$
begin
    if (TG_OP = 'DELETE') then
        insert into audit_log (table_name, record_id, action, old_data)
        values (TG_TABLE_NAME, OLD.id, 'DELETE', row_to_json(OLD));
        return OLD;
    elsif (TG_OP = 'UPDATE') then
        insert into audit_log (table_name, record_id, action, old_data, new_data)
        values (TG_TABLE_NAME, NEW.id, 'UPDATE', row_to_json(OLD), row_to_json(NEW));
        return NEW;
    elsif (TG_OP = 'INSERT') then
        insert into audit_log (table_name, record_id, action, new_data)
        values (TG_TABLE_NAME, NEW.id, 'INSERT', row_to_json(NEW));
        return NEW;
    end if;
end;
$$;

-- Apply audit triggers to key tables
drop trigger if exists audit_leases on leases;
create trigger audit_leases
    after insert or update or delete on leases
    for each row execute function audit_trigger_func();

drop trigger if exists audit_disputes on disputes;
create trigger audit_disputes
    after insert or update or delete on disputes
    for each row execute function audit_trigger_func();

drop trigger if exists audit_incidents on incidents;
create trigger audit_incidents
    after insert or update or delete on incidents
    for each row execute function audit_trigger_func();
