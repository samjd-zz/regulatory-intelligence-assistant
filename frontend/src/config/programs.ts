import { z } from "zod";

export type ProgramId = 
	| "employment-insurance"
	| "cpp-retirement"
	| "canada-child-benefit"
	| "gis"
	| "social-assistance";

export interface FieldConfig {
	name: string;
	label: string;
	type: "text" | "number" | "select" | "file";
	placeholder?: string;
	options?: Array<{ value: string; label: string }>;
	helpText?: string;
	min?: number;
	max?: number;
}

export interface ProgramConfig {
	id: ProgramId;
	name: string;
	description: string;
	fields: FieldConfig[];
	validationSchema: z.ZodObject<z.ZodRawShape>;
}

// Employment Insurance
const eiSchema = z.object({
	full_name: z
		.string()
		.min(2, "Name must be at least 2 characters")
		.max(100, "Name must be less than 100 characters"),
	sin: z
		.string()
		.regex(/^\d{3}-\d{3}-\d{3}$/, "SIN must be in format: 123-456-789")
		.length(11, "SIN must be exactly 11 characters including dashes"),
	residency_status: z.enum(
		["citizen", "permanent_resident", "temporary_resident"],
		{ message: "Please select a valid residency status" }
	),
	hours_worked: z
		.number()
		.int("Hours must be a whole number")
		.min(420, "Minimum 420 hours required for eligibility")
		.max(10000, "Hours worked seems unreasonably high"),
});

// CPP Retirement
const cppSchema = z.object({
	full_name: z.string().min(2).max(100),
	sin: z
		.string()
		.regex(/^\d{3}-\d{3}-\d{3}$/, "SIN must be in format: 123-456-789")
		.length(11),
	age: z
		.number()
		.int()
		.min(60, "Must be at least 60 years old")
		.max(120, "Invalid age"),
	years_of_contribution: z
		.number()
		.int()
		.min(1, "Must have at least 1 year of CPP contributions")
		.max(50, "Invalid years of contribution"),
});

// Canada Child Benefit
const ccbSchema = z.object({
	full_name: z.string().min(2).max(100),
	sin: z
		.string()
		.regex(/^\d{3}-\d{3}-\d{3}$/, "SIN must be in format: 123-456-789")
		.length(11),
	number_of_children: z
		.number()
		.int()
		.min(1, "Must have at least 1 child")
		.max(20, "Invalid number of children"),
	annual_income: z
		.number()
		.min(0, "Income cannot be negative")
		.max(10000000, "Invalid income amount"),
});

// Guaranteed Income Supplement
const gisSchema = z.object({
	full_name: z.string().min(2).max(100),
	sin: z
		.string()
		.regex(/^\d{3}-\d{3}-\d{3}$/, "SIN must be in format: 123-456-789")
		.length(11),
	age: z
		.number()
		.int()
		.min(65, "Must be at least 65 years old")
		.max(120, "Invalid age"),
	annual_income: z
		.number()
		.min(0, "Income cannot be negative")
		.max(1000000, "Income exceeds GIS eligibility threshold"),
});

// Social Assistance
const socialAssistanceSchema = z.object({
	full_name: z.string().min(2).max(100),
	address: z.string().min(5, "Address is required"),
	id_document: z.string().min(1, "Government ID is required"),
	proof_of_residency: z.string().min(1, "Proof of residency is required"),
});

export const PROGRAMS: Record<ProgramId, ProgramConfig> = {
	"employment-insurance": {
		id: "employment-insurance",
		name: "Employment Insurance (EI)",
		description: "Regular benefits for those who lost their job through no fault of their own",
		fields: [
			{
				name: "full_name",
				label: "Full Legal Name",
				type: "text",
				placeholder: "John Doe",
			},
			{
				name: "sin",
				label: "Social Insurance Number (SIN)",
				type: "text",
				placeholder: "000-000-000",
			},
			{
				name: "residency_status",
				label: "Residency Status",
				type: "select",
				options: [
					{ value: "citizen", label: "Canadian Citizen" },
					{ value: "permanent_resident", label: "Permanent Resident" },
					{
						value: "temporary_resident",
						label: "Temporary Resident (Work Permit)",
					},
				],
			},
			{
				name: "hours_worked",
				label: "Hours Worked (Last 52 Weeks)",
				type: "number",
				placeholder: "e.g. 600",
				min: 0,
				helpText: "Min. 420 hrs",
			},
		],
		validationSchema: eiSchema,
	},
	"cpp-retirement": {
		id: "cpp-retirement",
		name: "Canada Pension Plan (CPP) Retirement",
		description: "Monthly pension for contributors aged 60 and older",
		fields: [
			{
				name: "full_name",
				label: "Full Legal Name",
				type: "text",
				placeholder: "John Doe",
			},
			{
				name: "sin",
				label: "Social Insurance Number (SIN)",
				type: "text",
				placeholder: "000-000-000",
			},
			{
				name: "age",
				label: "Current Age",
				type: "number",
				placeholder: "e.g. 65",
				min: 60,
				max: 120,
				helpText: "Must be 60 or older",
			},
			{
				name: "years_of_contribution",
				label: "Years of CPP Contributions",
				type: "number",
				placeholder: "e.g. 35",
				min: 1,
				max: 50,
				helpText: "At least 1 year required",
			},
		],
		validationSchema: cppSchema,
	},
	"canada-child-benefit": {
		id: "canada-child-benefit",
		name: "Canada Child Benefit (CCB)",
		description: "Tax-free monthly payment for families with children under 18",
		fields: [
			{
				name: "full_name",
				label: "Full Legal Name",
				type: "text",
				placeholder: "John Doe",
			},
			{
				name: "sin",
				label: "Social Insurance Number (SIN)",
				type: "text",
				placeholder: "000-000-000",
			},
			{
				name: "number_of_children",
				label: "Number of Children Under 18",
				type: "number",
				placeholder: "e.g. 2",
				min: 1,
				max: 20,
			},
			{
				name: "annual_income",
				label: "Family Annual Income",
				type: "number",
				placeholder: "e.g. 45000",
				min: 0,
				helpText: "Total family income from previous tax year",
			},
		],
		validationSchema: ccbSchema,
	},
	gis: {
		id: "gis",
		name: "Guaranteed Income Supplement (GIS)",
		description: "Monthly benefit for low-income OAS recipients",
		fields: [
			{
				name: "full_name",
				label: "Full Legal Name",
				type: "text",
				placeholder: "John Doe",
			},
			{
				name: "sin",
				label: "Social Insurance Number (SIN)",
				type: "text",
				placeholder: "000-000-000",
			},
			{
				name: "age",
				label: "Current Age",
				type: "number",
				placeholder: "e.g. 67",
				min: 65,
				max: 120,
				helpText: "Must be 65 or older",
			},
			{
				name: "annual_income",
				label: "Annual Income",
				type: "number",
				placeholder: "e.g. 18000",
				min: 0,
				helpText: "Income from previous tax year",
			},
		],
		validationSchema: gisSchema,
	},
	"social-assistance": {
		id: "social-assistance",
		name: "Social Assistance",
		description: "Financial support for individuals and families in need",
		fields: [
			{
				name: "full_name",
				label: "Full Legal Name",
				type: "text",
				placeholder: "John Doe",
			},
			{
				name: "address",
				label: "Current Address",
				type: "text",
				placeholder: "123 Main St, City, Province, Postal Code",
			},
			{
				name: "id_document",
				label: "Government-Issued ID",
				type: "file",
				helpText: "Upload driver's license, passport, or other government ID",
			},
			{
				name: "proof_of_residency",
				label: "Proof of Residency",
				type: "file",
				helpText: "Upload utility bill, lease, or bank statement",
			},
		],
		validationSchema: socialAssistanceSchema,
	},
};

export const PROGRAM_LIST = Object.values(PROGRAMS);
