# You Do Not Have to Know How Many Steps

In [post 1](./01-basics.md) we chained `-[:KNOWS]->` twice to find a friend of
a friend. More often, though, **you do not know how many steps it takes.**

Here we write that kind of path in one line.

## 1. Say the data looks like this

People, restaurants and a city, joined by edges.

<img src="./restaurants.svg" alt="a graph running from me through Mina to restaurants in Lisbon"
     style="max-width:820px; width:100%; height:auto; display:block; margin:0 auto;">

`me` likes `Mina`, and `Mina` collaborated with `Olive Table`. `Jun` trained
under `Mina` and built the wine list at `Cork and Candle`.

We want **restaurants in Lisbon connected to someone I like**. It might be one
step away, it might be three.

## 2. One query

```
MATCH (me:Person {id: $userId})-[:LIKES]->(s:Person)
MATCH path = (s)-[:TRAINED_UNDER|COLLAB_WITH|BUILT_WINE_LIST*1..3]-(p:Place)
      -[:IN]->(:City {name: 'Lisbon'})
RETURN p.name,
       [r IN relationships(path) | type(r)] AS why,
       length(path) AS hops
ORDER BY hops
LIMIT 3
```

Only four things are new since post 1.

```
  path =                name the whole path that was found
  [:A|B|C]              an A or a B or a C edge
  *1..3                 one to three edges along the way -- distance 1 to 3
  relationships(path)   the list of edges on the path
```

The rest came up in post 1: `$userId`, two `MATCH` clauses, a node with no name
tag, `[x IN list | ...]`, `AS`, `ORDER BY`, `LIMIT`.

## 3. Line by line

### The first MATCH

```
  (me:Person {id: $userId})    the Person whose id is $userId, called me
  -[:LIKES]->(s:Person)        whoever me LIKES, called s
```

In the picture, `s` is `Mina`.

### The second MATCH

This is the heart of the post.

```
  *1..3                  distance 1 to 3 will do. You need not know which
  the end is - not ->    direction is ignored
  [:A|B|C]               any of the three types
  (p:Place)              the destination is a restaurant, tagged p
  -[:IN]->(:City {...})  it has to be in Lisbon
```

**Without `*1..3` you would write one query for one step, another for two and
another for three.** And as post 1 showed, **you may mix the three types** —
that is how path B below qualifies.

The `-` at the end also means **you can walk backwards.** The edge saying `Jun`
trained under `Mina` points `Jun → Mina`, but you can start at `Mina` and go
back up it to `Jun`.

The city is never returned, so `(:City ...)` has no name tag — the same slot
you saw in post 1.

Two paths qualify.

```
  A   Mina --COLLAB_WITH--> Olive Table --IN--> Lisbon            2 edges
  B   Mina <--TRAINED_UNDER-- Jun
           --BUILT_WINE_LIST--> Cork and Candle --IN--> Lisbon    3 edges
```

### RETURN

```
  p.name                   the restaurant name
  relationships(path)      the list of edges on the path
  [r IN list | type(r)]    take only the type name of each edge
  length(path)             how many edges the whole path has -- the distance
```

## 4. The result

```
p.name              why                                        hops
"Olive Table"       ["COLLAB_WITH", "IN"]                      2
"Cork and Candle"   ["TRAINED_UNDER", "BUILT_WINE_LIST", "IN"] 3
```

`hops` looks like it exceeds the range in `*1..3`, and it does. **The star
binds only the middle segment, while `length(path)` counts the closing
`-[:IN]->` as well.** Path B is two in the middle plus the one `IN`.

**`why` is the useful column.** Hand back only a restaurant name and you cannot
explain why you recommended it; with the edge types alongside, you can say
*"Olive Table collaborated with Mina, who you like."*

## 5. In SQL

That single `*1..3` becomes **a one-step JOIN, a two-step JOIN and a three-step
JOIN, combined with `UNION`** — or you reach for `WITH RECURSIVE`. Add the
three edge types and the ignored direction and it grows further.

## A note

**Raising the numbers in `*1..3` gets slow.** The number of walkable paths
grows at every step. Better to write down a range you will actually use.
