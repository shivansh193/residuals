import * as s from "../../core/validation/index.js";
import type { Schema } from "../../core/validation/schema.js";
import { invoiceOutSchema, type InvoiceOut } from "../invoice-out.js";

export type Invoice = InvoiceOut;

export const invoiceSchema: Schema<Invoice> = s.of<Invoice>(s.union([s.lazy(() => invoiceOutSchema)]));
