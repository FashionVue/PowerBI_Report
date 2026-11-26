using System;
using System.Linq;
using Microsoft.AnalysisServices.Tabular;

class P {
    static int Main(string[] a) {
        try {
            var db = TmdlSerializer.DeserializeDatabaseFromFolder(a[0]);
            var m = db.Model;
            Console.WriteLine($"Database '{db.Name}' compat={db.CompatibilityLevel} culture={m.Culture}");
            foreach (var e in m.Expressions) Console.WriteLine($"  expression {e.Name} kind={e.Kind}: {e.Expression}");
            foreach (var t in m.Tables) {
                Console.WriteLine($"  table {t.Name} dataCategory={t.DataCategory} desc='{t.Description}'");
                foreach (var c in t.Columns) Console.WriteLine($"    col {c.Name} type={c.DataType} key={c.IsKey} hidden={c.IsHidden} fmt={c.FormatString} summ={c.SummarizeBy} sortBy={(c.SortByColumn?.Name ?? "-")} src={(c as DataColumn)?.SourceColumn}");
                foreach (var ms in t.Measures) Console.WriteLine($"    measure [{ms.Name}] fmt={ms.FormatString} folder={ms.DisplayFolder} desc='{ms.Description}'\n      {ms.Expression.Replace("\n", "\n      ")}");
                foreach (var p in t.Partitions) Console.WriteLine($"    partition {p.Name} mode={p.Mode} source={p.Source.GetType().Name}\n      {((MPartitionSource)p.Source).Expression.Replace("\n", "\n      ")}");
            }
            foreach (SingleColumnRelationship r in m.Relationships)
                Console.WriteLine($"  rel {r.FromTable.Name}[{r.FromColumn.Name}] {r.FromCardinality} -> {r.ToTable.Name}[{r.ToColumn.Name}] {r.ToCardinality} filter={r.CrossFilteringBehavior} active={r.IsActive} types={r.FromColumn.DataType}/{r.ToColumn.DataType}");
            foreach (var an in m.Annotations) Console.WriteLine($"  model annotation {an.Name} = {an.Value}");
            if (a.Length > 1) { TmdlSerializer.SerializeDatabaseToFolder(db, a[1]); Console.WriteLine("re-serialized to " + a[1]); }
            return 0;
        } catch (Exception ex) {
            Console.WriteLine("TMDL ERROR: " + ex);
            return 1;
        }
    }
}
