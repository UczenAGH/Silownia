#  1. Instalacja i konfiguracja

```bash
pip install supabase
```

---

## Import i połączenie

```python
from supabase import create_client, Client

url = "https://YOUR_PROJECT_ID.supabase.co"
key = "YOUR_ANON_OR_SERVICE_KEY"

supabase: Client = create_client(url, key)
```

---

#  2. Operacje na tabelach (Database CRUD)

## ➜ SELECT — pobieranie danych

### Pobierz wszystko

```python
response = supabase.table("users").select("*").execute()
print(response.data)
```

---

### Wybór konkretnych kolumn

```python
supabase.table("users") \
    .select("id, name") \
    .execute()
```

---

### WHERE (filtry)

```python
supabase.table("users") \
    .select("*") \
    .eq("id", 1) \
    .execute()
```

---

### Inne operatory filtrów

```python
.eq("age", 18)        # =
.neq("age", 18)       # !=
.gt("age", 18)        # >
.gte("age", 18)       # >=
.lt("age", 18)        # <
.lte("age", 18)       # <=
.like("name", "%Jan%")
.ilike("name", "%jan%")
.is_("deleted", None)
.in_("role", ["admin", "user"])
```

---

### Limit i sortowanie

```python
supabase.table("users") \
    .select("*") \
    .order("created_at", desc=True) \
    .limit(10) \
    .execute()
```

---

##  INSERT — dodawanie danych

```python
data = {
    "name": "Jan",
    "age": 25
}

supabase.table("users").insert(data).execute()
```

---

### Insert wielu rekordów

```python
supabase.table("users").insert([
    {"name": "Anna"},
    {"name": "Piotr"}
]).execute()
```

---

##  UPDATE — aktualizacja

```python
supabase.table("users") \
    .update({"name": "Nowe imię"}) \
    .eq("id", 1) \
    .execute()
```

---

##  DELETE — usuwanie

```python
supabase.table("users") \
    .delete() \
    .eq("id", 1) \
    .execute()
```

---

#  3. Single row (jednoznaczny rekord)

```python
supabase.table("users") \
    .select("*") \
    .eq("id", 1) \
    .single() \
    .execute()
```

---

#  4. Authentication (Auth)

## Rejestracja użytkownika

```python
supabase.auth.sign_up({
    "email": "user@email.com",
    "password": "password123"
})
```

---

## Logowanie

```python
supabase.auth.sign_in_with_password({
    "email": "user@email.com",
    "password": "password123"
})
```

---

## Wylogowanie

```python
supabase.auth.sign_out()
```

---

## Aktualny użytkownik

```python
user = supabase.auth.get_user()
```

---

#  5. Storage (pliki)

## Upload pliku

```python
with open("photo.png", "rb") as f:
    supabase.storage.from_("images").upload(
        "photo.png",
        f
    )
```

---

## Pobranie public URL

```python
supabase.storage.from_("images").get_public_url("photo.png")
```

---

## Usunięcie pliku

```python
supabase.storage.from_("images").remove(["photo.png"])
```

---

#  6. RPC — wywołanie funkcji SQL

Jeśli masz funkcję w PostgreSQL:

```sql
create function get_users_count()
returns int
language sql
as $$
  select count(*) from users;
$$;
```

Python:

```python
supabase.rpc("get_users_count").execute()
```

---

#  7. Upsert (insert lub update)

```python
supabase.table("users").upsert({
    "id": 1,
    "name": "Jan"
}).execute()
```

---

#  8. Count rekordów

```python
supabase.table("users") \
    .select("*", count="exact") \
    .execute()
```

---

#  9. Transforms / range (paginacja)

```python
supabase.table("users") \
    .select("*") \
    .range(0, 9) \
    .execute()
```

---

#  10. Obsługa błędów

```python
response = supabase.table("users").select("*").execute()

if response.data:
    print(response.data)
else:
    print(response.error)
```

---

#  Najczęściej używany workflow (realny przykład)

```python
users = (
    supabase.table("users")
    .select("*")
    .eq("active", True)
    .order("created_at", desc=True)
    .limit(5)
    .execute()
)
```


