const { z } = require('zod');

const DEFAULT_LIMIT_MODEL = 100;

const optionalTrimmedString = (min, max) =>
  z.string().trim().min(min).max(max).nullable().optional();

const normalizeFlightInput = (input = {}) => ({
  ...input,
  scheduled_departure:
    input.scheduled_departure ?? input.departure_info ?? input.arrival_info,
  scheduled_arrival:
    input.scheduled_arrival ?? input.arrival_info ?? input.departure_info
});

const FlightBaseSchema = z.object({
  id_flight: optionalTrimmedString(8, 10),
  number: optionalTrimmedString(1, 16)
}).passthrough();

const FlightSchema = FlightBaseSchema.extend({
  origin: optionalTrimmedString(1, 120),
  origin_iata: optionalTrimmedString(3, 8),
  destination: optionalTrimmedString(1, 120),
  destination_iata: optionalTrimmedString(3, 8),
  scheduled_departure: optionalTrimmedString(1, 40),
  utc_departure: z.number().int().nullable().optional(),
  scheduled_arrival: optionalTrimmedString(1, 40),
  utc_arrival: z.number().int().nullable().optional()
}).passthrough();

const FlightDetailSchema = FlightSchema.extend({
  lat: z.number().nullable().optional(),
  lon: z.number().nullable().optional()
}).passthrough();

const FlightQuerySchema = z.object({
  iata: z.string().trim().min(1),
  type: z.number().int().default(1),
  limit: z.number().int().default(DEFAULT_LIMIT_MODEL),
  page: z.number().int().default(1),
  asc: z.number().int().default(1)
});

const parseFlight = (input) => FlightSchema.parse(normalizeFlightInput(input));

const parseFlightDetail = (input) =>
  FlightDetailSchema.parse(normalizeFlightInput(input));

module.exports = {
  DEFAULT_LIMIT_MODEL,
  normalizeFlightInput,
  FlightBaseSchema,
  FlightSchema,
  FlightDetailSchema,
  FlightQuerySchema,
  parseFlight,
  parseFlightDetail
};