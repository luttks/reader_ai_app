export default function ChapterList({
    chapters,
    selectedChapterId,
    onSelectChapter,
  }) {
    return (
      <div className="card">
        <h2>Chapters</h2>
        {chapters.length === 0 ? (
          <p className="muted">No chapters available.</p>
        ) : (
          <ul className="list">
            {chapters.map((chapter) => (
              <li key={chapter.id}>
                <button
                  className={
                    selectedChapterId === chapter.id ? "list-item active" : "list-item"
                  }
                  onClick={() => onSelectChapter(chapter.id)}
                >
                  <div className="list-title">
                    {chapter.chapter_index}. {chapter.title}
                  </div>
                  <div className="list-meta">
                    {chapter.paragraph_count} paragraphs • {chapter.sentence_count} sentences
                  </div>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    );
  }