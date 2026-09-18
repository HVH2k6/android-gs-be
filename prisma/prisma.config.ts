// Prisma 7 Configuration (datasource URL moved from schema.prisma)
// https://pris.ly/d/config-datasource

import { defineConfig } from '@prisma/client';

export default defineConfig({
  datasources: {
    db: {
      url: process.env.DATABASE_URL || 'postgresql://user:password@localhost:5432/gs_android_learning',
    },
  },
});
