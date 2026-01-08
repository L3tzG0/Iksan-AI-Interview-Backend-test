# Frontend Pagination Implementation Guide

This guide explains how to implement pagination for API requests to the Iksan AI Interview Backend.

## Overview

All paginated endpoints return a standardized response structure that includes:
- **items**: Array of requested data
- **total**: Total number of matching records
- **skip**: Number of records skipped
- **limit**: Maximum records requested per page
- **has_more**: Boolean indicating if more records exist after current page

## Request Parameters

When calling a paginated endpoint, include these query parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `skip` | integer | 0 | Number of records to skip (0-based offset) |
| `limit` | integer | 20 | Maximum records to return (1-100) |

**Example:**
```
GET /api/v1/classes?skip=0&limit=20
GET /api/v1/students?skip=20&limit=20
```

## Response Format

All paginated responses follow this structure:

```json
{
  "items": [...],
  "total": 150,
  "skip": 0,
  "limit": 20,
  "has_more": true
}
```

## Implementation Examples

### React Example

```typescript
const [items, setItems] = useState([]);
const [total, setTotal] = useState(0);
const [skip, setSkip] = useState(0);
const LIMIT = 20;

const fetchItems = async (offset: number) => {
  try {
    const response = await fetch(
      `/api/v1/classes?skip=${offset}&limit=${LIMIT}`
    );
    const data = await response.json();
    
    setItems(data.items);
    setTotal(data.total);
    setSkip(offset);
  } catch (error) {
    console.error('Error fetching items:', error);
  }
};

// Initial load
useEffect(() => {
  fetchItems(0);
}, []);

// Pagination buttons
const handleNextPage = () => {
  if (skip + LIMIT < total) {
    fetchItems(skip + LIMIT);
  }
};

const handlePreviousPage = () => {
  if (skip > 0) {
    fetchItems(Math.max(0, skip - LIMIT));
  }
};
```

### Vue Example

```vue
<script>
export default {
  data() {
    return {
      items: [],
      total: 0,
      skip: 0,
      limit: 20
    }
  },
  methods: {
    async fetchItems(offset) {
      try {
        const response = await fetch(
          `/api/v1/classes?skip=${offset}&limit=${this.limit}`
        );
        const data = await response.json();
        this.items = data.items;
        this.total = data.total;
        this.skip = offset;
      } catch (error) {
        console.error('Error fetching items:', error);
      }
    },
    nextPage() {
      if (this.skip + this.limit < this.total) {
        this.fetchItems(this.skip + this.limit);
      }
    },
    previousPage() {
      if (this.skip > 0) {
        this.fetchItems(Math.max(0, this.skip - this.limit));
      }
    }
  },
  mounted() {
    this.fetchItems(0);
  }
}
</script>

<template>
  <div>
    <div class="items-list">
      <div v-for="item in items" :key="item.id">{{ item }}</div>
    </div>
    
    <div class="pagination">
      <button @click="previousPage" :disabled="skip === 0">Previous</button>
      <span>Page {{ Math.floor(skip / limit) + 1 }} of {{ Math.ceil(total / limit) }}</span>
      <button @click="nextPage" :disabled="!has_more">Next</button>
    </div>
  </div>
</template>
```

## Common Patterns

### Calculate Current Page Number
```javascript
const currentPage = Math.floor(skip / limit) + 1;
```

### Calculate Total Pages
```javascript
const totalPages = Math.ceil(total / limit);
```

### Check if Next Page Exists
```javascript
const hasNextPage = (skip + limit) < total;
// Or use the has_more flag from response
const hasNextPage = data.has_more;
```

## Endpoints with Pagination

These endpoints support pagination:
- `GET /api/v1/users` - List users
- `GET /api/v1/classes` - List classes
- `GET /api/v1/schools` - List schools
- `GET /api/v1/majors` - List majors
- `GET /api/v1/sessions` - List interview sessions (for students)
- `GET /api/v1/sessions/all` - List interview sessions (for admins and teachers)

Check the API documentation for complete endpoint details.

## Tips & Best Practices

1. **Always respect the `limit` parameter range** (1-100)
2. **Use `has_more` flag** to determine if more records exist instead of calculating manually
3. **Cache results** to avoid unnecessary API calls when navigating between pages
4. **Show loading states** while fetching data
5. **Handle errors gracefully** and allow users to retry
6. **Default to `limit=20`** unless UX requires a different value

## Troubleshooting

**No items returned?**
- Verify `skip` value is within valid range
- Check if filters/search criteria are applied correctly

**Getting fewer items than `limit`?**
- This is normal on the last page - use `has_more` to detect this

**Wrong page calculation?**
- Use the provided `skip` and `limit` values to calculate pages, not `total`

