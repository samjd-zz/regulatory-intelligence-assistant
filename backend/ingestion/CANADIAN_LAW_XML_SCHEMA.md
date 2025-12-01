# Canadian Law XML Schema Documentation

Source: https://github.com/justicecanada/laws-lois-xml

## Namespace

All Canadian law XML files use the LIMS namespace:
```xml
xmlns:lims="http://justice.gc.ca/lims"
```

## Root Elements

### Acts (Statutes)
```xml
<Statute lims:pit-date="..." hasPreviousVersion="..." lims:lastAmendedDate="..." 
         lims:current-date="..." lims:inforce-start-date="..." lims:fid="..." 
         lims:id="..." bill-origin="..." bill-type="..." in-force="..." 
         xml:lang="en|fr">
```

### Regulations
```xml
<Regulation lims:pit-date="..." hasPreviousVersion="..." lims:lastAmendedDate="..." 
            lims:current-date="..." lims:inforce-start-date="..." lims:fid="..." 
            lims:id="..." regulation-type="..." xml:lang="en|fr">
```

## Structure for Acts (Statutes)

### Identification Section
```xml
<Identification>
    <LongTitle>Full official title of the Act</LongTitle>
    <ShortTitle status="official">Short Title Act</ShortTitle>
    <RunningHead>Running Head</RunningHead>
    <BillHistory>
        <Stages stage="consolidation">
            <Date>
                <YYYY>2024</YYYY>
                <MM>1</MM>
                <DD>24</DD>
            </Date>
        </Stages>
    </BillHistory>
    <Chapter>
        <ConsolidatedNumber official="yes">A-1</ConsolidatedNumber>
    </Chapter>
</Identification>
```

### Body Section
```xml
<Body>
    <Heading level="1">
        <TitleText>Part Title</TitleText>
    </Heading>
    
    <Section lims:fid="..." lims:id="...">
        <MarginalNote>Section title</MarginalNote>
        <Label>1</Label>
        <Text>Section content...</Text>
        
        <Subsection lims:fid="..." lims:id="...">
            <MarginalNote>Subsection title (optional)</MarginalNote>
            <Label>(1)</Label>
            <Text>Subsection content...</Text>
            
            <Paragraph lims:fid="..." lims:id="...">
                <Label>(a)</Label>
                <Text>Paragraph content...</Text>
            </Paragraph>
        </Subsection>
        
        <HistoricalNote>
            <HistoricalNoteSubItem>Amendment history</HistoricalNoteSubItem>
        </HistoricalNote>
    </Section>
    
    <Section>
        <MarginalNote>Definitions</MarginalNote>
        <Label>2</Label>
        <Text>In this Act,</Text>
        <Definition>
            <Text><DefinedTermEn>term</DefinedTermEn> means... (<DefinedTermFr>terme</DefinedTermFr>)</Text>
        </Definition>
    </Section>
</Body>
```

### Schedule Section
```xml
<Schedule lims:fid="..." lims:id="..." bilingual="no" spanlanguages="yes">
    <ScheduleFormHeading>
        <Label>SCHEDULE I</Label>
        <OriginatingRef>(Section 5)</OriginatingRef>
    </ScheduleFormHeading>
    <TableGroup>
        <table>...</table>
    </TableGroup>
    <HistoricalNote>...</HistoricalNote>
</Schedule>
```

### Recent Amendments
```xml
<RecentAmendments>
    <Amendment>
        <AmendmentCitation link="2023_29">2023, c. 29</AmendmentCitation>
        <AmendmentDate>2024-01-22</AmendmentDate>
    </Amendment>
</RecentAmendments>
```

## Structure for Regulations

### Identification Section
```xml
<Identification>
    <InstrumentNumber>SOR/97-175</InstrumentNumber>
    <RegistrationDate>
        <Date>
            <YYYY>1997</YYYY>
            <MM>4</MM>
            <DD>8</DD>
        </Date>
    </RegistrationDate>
    <ConsolidationDate>
        <Date>
            <YYYY>2024</YYYY>
            <MM>2</MM>
            <DD>7</DD>
        </Date>
    </ConsolidationDate>
    <EnablingAuthority>
        <XRefExternal reference-type="act" link="D-3.4">DIVORCE ACT</XRefExternal>
    </EnablingAuthority>
    <LongTitle>Full Title of Regulation</LongTitle>
    <ShortTitle>Short Title (optional)</ShortTitle>
    <RegulationMakerOrder>
        <RegulationMaker>P.C.</RegulationMaker>
        <OrderNumber>1997-469</OrderNumber>
        <Date>...</Date>
    </RegulationMakerOrder>
</Identification>
```

### Order Section (for some regulations)
```xml
<Order>
    <Provision format-ref="..." language-align="yes" list-item="no">
        <Text>Order-making text with <FootnoteRef idref="...">a</FootnoteRef></Text>
        <Footnote id="..." placement="page" status="official">
            <Label>a</Label>
            <Text>Footnote text</Text>
        </Footnote>
    </Provision>
</Order>
```

### Body Section (similar to Acts)
Same structure as Acts Body section.

## Key Elements

### Cross-References
```xml
<XRefExternal reference-type="act|regulation|section" link="...">Text</XRefExternal>
```

### Repealed Sections
```xml
<Text><Repealed>[Repealed, SOR/94-289, s. 1]</Repealed></Text>
```

### Bilingual Terms
```xml
<DefinedTermEn>English term</DefinedTermEn>
<DefinedTermFr>terme français</DefinedTermFr>
```

### Historical Notes
```xml
<HistoricalNote>
    <HistoricalNoteSubItem lims:inforce-start-date="..." lims:enacted-date="..." 
                           lims:fid="..." lims:id="..." lims:enactId="...">
        Amendment citation
    </HistoricalNoteSubItem>
</HistoricalNote>
```

## Important Attributes

- `lims:fid` - Fragment ID (unique identifier for element)
- `lims:id` - LIMS ID (database ID)
- `lims:pit-date` - Point-in-time date
- `lims:inforce-start-date` - When this version came into force
- `lims:lastAmendedDate` - Date of last amendment
- `lims:current-date` - Current consolidation date
- `lims:enacted-date` - Original enactment date
- `lims:enactId` - Enactment ID for tracking amendments
- `xml:lang` - Language ("en" or "fr")

## Element Nesting Hierarchy

```
Statute/Regulation
├── Identification
├── Order (regulations only)
├── Body
│   ├── Heading (level 1, 2, 3...)
│   └── Section
│       ├── MarginalNote
│       ├── Label
│       ├── Text
│       ├── Subsection
│       │   ├── MarginalNote (optional)
│       │   ├── Label
│       │   ├── Text
│       │   └── Paragraph
│       │       ├── Label
│       │       ├── Text
│       │       └── Subparagraph (can nest further)
│       ├── Definition
│       └── HistoricalNote
├── Schedule (can have multiple)
│   ├── ScheduleFormHeading
│   ├── RegulationPiece or direct Sections
│   └── HistoricalNote
└── RecentAmendments
    └── Amendment (multiple)
