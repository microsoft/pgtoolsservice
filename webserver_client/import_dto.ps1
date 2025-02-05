# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# Run json2ts to convert JSON Schema to TypeScript definitions
npx json-schema-to-typescript --input ../build/dto_generator/full_schema.json --output src/full_schema.d.ts