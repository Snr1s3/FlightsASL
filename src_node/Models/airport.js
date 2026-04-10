const { z } = require('zod');

const AirportSchema = z.object({
  name: z.string(),
  iata: z.string().nullable().optional(),
  icao: z.string().nullable().optional(),
  lat: z.number().nullable().optional(),
  lon: z.number().nullable().optional(),
  search: z.boolean().optional().default(false)
});

const AirportSearchRequestSchema = z.object({
  name: z.string().min(1)
});

module.exports = {
  AirportSchema,
  AirportSearchRequestSchema
};