import {
  QueryComponent,
  QueryResultsPaneComponent,
  QueryToolbarComponent,
} from "@trident/relational-db-ux/lib/queries";
import {
  EditorComponent,
  NarrowedLanguageServiceConfig,
} from "@trident/relational-db-ux/lib/monaco-editor";

const languageService: NarrowedLanguageServiceConfig = {
  syntaxHighlightRule: {
    defaultToken: "",
    ignoreCase: true,
    brackets: [
      { open: "[", close: "]", token: "delimiter.square" },
      { open: "(", close: ")", token: "delimiter.parenthesis" },
    ],
    ReservedKeywords: [],
    operators: ["select", "from", "where", "group by", "order by", "having"],
    builtinFunctions: ["abs"],
    builtinVariables: ["$table"],
    tokenizer: {
      root: [
        [
          /[a-zA-Z_][\w]*/,
          {
            cases: {
              "@keywords": "keyword",
              "@default": "identifier",
            },
          },
        ],
        { include: "@whitespace" },
        [/[0-9]+/, "number"],
        [/[;,.]/, "delimiter"],
        [/".*?"/, "string"],
        [/--.*$/, "comment"],
      ],

      whitespace: [[/\s+/, "white"]],
    },
  },
};

export const QueryEditorComponent = () => {
  const q = (
    <QueryComponent
      getEditorComponent={(props) => (
        <EditorComponent
          {...props}
          language="TSQL"
          languageServiceConfig={languageService}
          onEditorCertifiedEvent={(
            feature,
            activity,
            additionalAttributes?,
            error?
          ) => {
            console.log(feature, activity, additionalAttributes, error);
          }}
        />
      )}
      getQueryResultsPaneComponent={() => (
        <QueryResultsPaneComponent maxHeight={500} />
      )}
      getQueryToolbarComponent={() => <QueryToolbarComponent />}
      getBanner={() => <></>}
      getStatusBarComponent={() => <></>}
    />
  );

  return <div style={{ height: 500 }}>{q}</div>;
};
