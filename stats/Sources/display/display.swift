import ArgumentParser
import Foundation

public struct Work: Codable {
    let workID: String
    let title: String
    let rating: String
    let authors: [String]
    let giftees: [String]
    let fandoms: [String]
    let series: [String: Int]
    let wordCount: Int
    let viewCount: Int
    let chapters: String
    let lastVisit: String
    let mostRecentUpdate: String
    let changesSinceLastView: String
    let markedForLater: Bool
    let complete: Bool
    let relationships: [String]
    let characters: [String]
    let tags: [String]

    enum CodingKeys: String, CodingKey {
        case workID = "work_id"
        case title, rating, authors, giftees, fandoms, series
        case wordCount = "word_count"
        case viewCount = "view_count"
        case chapters
        case lastVisit = "last_visit"
        case mostRecentUpdate = "most_recent_update"
        case changesSinceLastView = "changes_since_last_view"
        case markedForLater = "marked_for_later"
        case complete, relationships, characters, tags
    }
}

@main
public struct DisplayStats: ParsableCommand {
    @Argument var worksFile: String = "works.json"
    @Option var author: String? = nil
    @Option var fandom: String? = nil
    @Option var work: String? = nil

    @Option var mostReadN: Int? = nil

    public init() {}

    public func run() throws {
        let url = URL(fileURLWithPath: worksFile)
        let data: Data
        do {
            data = try Data(contentsOf: url)
        } catch {
            print("Unable to read contents of file!")
            throw ExitCode.failure
        }
        let allWorks: [Work]
        do {
            allWorks = try JSONDecoder().decode([Work].self, from: data)
        } catch let e {
            print("Unable to decode JSON")
            print(e)
            throw ExitCode.failure
        }

        let works = allWorks.filter { (!$0.markedForLater) }
        let markedForLater = allWorks.filter { $0.markedForLater }

        guard let longestWork = works.max(by: { $0.wordCount < $1.wordCount }) else {
            fatalError()
        }
        let byVC = works.sorted(by: { $0.viewCount > $1.viewCount })
        let mostReadFic = byVC[0]
        let byProduct = works.sorted(by: { $0.viewCount * $0.wordCount > $1.viewCount * $1.wordCount })
        let mostReadFicByWordCount = byProduct[0]
        let uniqueFicCount = works.count
        let ficCount = works.map(\.viewCount).sum
        let uniqueWordCount = works.map(\.wordCount).sum
        let wordCount = works.map { $0.wordCount * $0.viewCount }.sum

        print("""
              uniq_fic_count: \(uniqueFicCount) (\(markedForLater.count) marked for later)
              fic_count: \(ficCount)
              uniq_word_count: \(uniqueWordCount)
              word_count: \(wordCount)
              most_read_fic: "\(mostReadFic.title)" by \(mostReadFic.authors.joined(separator: ", ")) (\(mostReadFic.viewCount)x)
              most_read_fic_by_word_count: "\(mostReadFicByWordCount.title)" by \(mostReadFicByWordCount.authors.joined(separator: ", ")) (\(mostReadFicByWordCount.viewCount)x \(mostReadFicByWordCount.wordCount) words = \(mostReadFicByWordCount.viewCount * mostReadFicByWordCount.wordCount) words)
              longest_fic: "\(longestWork.title)" by \(longestWork.authors.joined(separator: ", ")) (\(longestWork.wordCount) words)
              """)
        print("===")

        if let n = mostReadN {
            for i in 1..<n {
                print("""
                most_read_fic [\(i)]: "\(byVC[i].title)" by \(byVC[i].authors.joined(separator: ", ")) (\(byVC[i].viewCount)x)
                most_read_fic_by_word_count [\(i)]: "\(byProduct[i].title)" by \(byProduct[i].authors.joined(separator: ", ")) (\(byProduct[i].viewCount)x \(byProduct[i].wordCount) words = \(byProduct[i].viewCount * byProduct[i].wordCount) words)
                """)
            }
            print("===")
        }

        var authorsToWorks = [String: [Work]]()
        var fandomsToWorks = [String: [Work]]()
        var relationshipsToWorks = [String: [Work]]()
        var charactersToWorks = [String: [Work]]()
        var tagsToWorks = [String: [Work]]()
        for work in works {
            for author in work.authors {
                authorsToWorks[author, default: []].append(work)
            }
            for fandom in work.fandoms {
                fandomsToWorks[fandom, default: []].append(work)
            }
            for relationship in work.relationships {
                relationshipsToWorks[relationship, default: []].append(work)
            }
            for character in work.characters {
                charactersToWorks[character, default: []].append(work)
            }
            for tag in work.tags {
                tagsToWorks[tag, default: []].append(work)
            }
        }
//        print(authorsToWorks.mapValues(\.count).sorted { $0.value > $1.value }.map { "\($0): \($1)" }.joined(separator: "\n"))
//        print(fandomsToWorks.mapValues(\.count).sorted { $0.value > $1.value }.map { "\($0): \($1)" }.joined(separator: "\n"))

        func generateStringForAuthor(_ author: String) -> String {
            let fics = authorsToWorks[author]!
            let uniqFicCount = fics.count
            let ficCount = fics.map(\.viewCount).sum
            let uniqWordCount = fics.map(\.wordCount).sum
            let wordCount = fics.map { $0.wordCount * $0.viewCount }.sum
            return "\(author): \(uniqFicCount) fics (read \(ficCount) times), totalling \(uniqWordCount) words (\(wordCount) words read)"
        }
        func topAuthorsByProperty(mapper: ([Work]) -> Int, title: String) {
            print("Top authors (\(title)):")
            let authorsByProperty = authorsToWorks.mapValues(mapper).sorted{ $0.value > $1.value }
            let topAuthorsByProperty = authorsByProperty.prefix(5).map { author, prop -> String in author }
            let topAuthorsByPropertyStrings = topAuthorsByProperty.map(generateStringForAuthor)
            print(topAuthorsByPropertyStrings.joined(separator: "\n"))
        }

        topAuthorsByProperty(mapper: \.count, title: "unique fics")
        print("---")
        topAuthorsByProperty(mapper: { $0.map(\.viewCount).sum }, title: "total reads")
        print("---")
        topAuthorsByProperty(mapper: { $0.map(\.wordCount).sum }, title: "unique words read")
        print("---")
        topAuthorsByProperty(mapper: { $0.map { $0.wordCount * $0.viewCount }.sum }, title: "total words read")

        print("===")

        func generateStringForFandom(_ fandom: String) -> String {
            let fics = fandomsToWorks[fandom]!
            let uniqFicCount = fics.count
            let ficCount = fics.map(\.viewCount).sum
            let uniqWordCount = fics.map(\.wordCount).sum
            let wordCount = fics.map { $0.wordCount * $0.viewCount }.sum
            return "\(fandom): \(uniqFicCount) fics (read \(ficCount) times), totalling \(uniqWordCount) words (\(wordCount) words read)"
        }
        func topFandomsByProperty(mapper: ([Work]) -> Int, title: String) {
            print("Top fandoms (\(title)):")
            let fandomsByProperty = fandomsToWorks.mapValues(mapper).sorted{ $0.value > $1.value }
            let topFandomsByProperty = fandomsByProperty.prefix(5).map { fandom, prop -> String in fandom }
            let topFandomsByPropertyStrings = topFandomsByProperty.map(generateStringForFandom)
            print(topFandomsByPropertyStrings.joined(separator: "\n"))
        }

        topFandomsByProperty(mapper: \.count, title: "unique fics")
        print("---")
        topFandomsByProperty(mapper: { $0.map(\.viewCount).sum }, title: "total reads")
        print("---")
        topFandomsByProperty(mapper: { $0.map(\.wordCount).sum }, title: "unique words read")
        print("---")
        topFandomsByProperty(mapper: { $0.map { $0.wordCount * $0.viewCount }.sum }, title: "total words read")

        print("===")
        func generateStringForRelationship(_ relationship: String) -> String {
            let fics = relationshipsToWorks[relationship]!
            let uniqFicCount = fics.count
            let ficCount = fics.map(\.viewCount).sum
            let uniqWordCount = fics.map(\.wordCount).sum
            let wordCount = fics.map { $0.wordCount * $0.viewCount }.sum
            return "\(relationship): \(uniqFicCount) fics (read \(ficCount) times), totalling \(uniqWordCount) words (\(wordCount) words read)"
        }
        func topRelationshipsByProperty(mapper: ([Work]) -> Int, title: String) {
            print("Top relationships (\(title)):")
            let relationshipsByProperty = relationshipsToWorks.mapValues(mapper).sorted{ $0.value > $1.value }
            let topRelationshipsByProperty = relationshipsByProperty.prefix(5).map { relationship, prop -> String in relationship }
            let topRelationshipsByPropertyStrings = topRelationshipsByProperty.map(generateStringForRelationship)
            print(topRelationshipsByPropertyStrings.joined(separator: "\n"))
        }

        topRelationshipsByProperty(mapper: \.count, title: "unique fics")
        print("---")
        topRelationshipsByProperty(mapper: { $0.map(\.viewCount).sum }, title: "total reads")
        print("---")
        topRelationshipsByProperty(mapper: { $0.map(\.wordCount).sum }, title: "unique words read")
        print("---")
        topRelationshipsByProperty(mapper: { $0.map { $0.wordCount * $0.viewCount }.sum }, title: "total words read")

        print("===")
        func generateStringForCharacter(_ character: String) -> String {
            let fics = charactersToWorks[character]!
            let uniqFicCount = fics.count
            let ficCount = fics.map(\.viewCount).sum
            let uniqWordCount = fics.map(\.wordCount).sum
            let wordCount = fics.map { $0.wordCount * $0.viewCount }.sum
            return "\(character): \(uniqFicCount) fics (read \(ficCount) times), totalling \(uniqWordCount) words (\(wordCount) words read)"
        }
        func topCharactersByProperty(mapper: ([Work]) -> Int, title: String) {
            print("Top characters (\(title)):")
            let charactersByProperty = charactersToWorks.mapValues(mapper).sorted{ $0.value > $1.value }
            let topCharactersByProperty = charactersByProperty.prefix(5).map { character, prop -> String in character }
            let topCharactersByPropertyStrings = topCharactersByProperty.map(generateStringForCharacter)
            print(topCharactersByPropertyStrings.joined(separator: "\n"))
        }

        topCharactersByProperty(mapper: \.count, title: "unique fics")
        print("---")
        topCharactersByProperty(mapper: { $0.map(\.viewCount).sum }, title: "total reads")
        print("---")
        topCharactersByProperty(mapper: { $0.map(\.wordCount).sum }, title: "unique words read")
        print("---")
        topCharactersByProperty(mapper: { $0.map { $0.wordCount * $0.viewCount }.sum }, title: "total words read")

        print("===")
        func generateStringForTag(_ tag: String) -> String {
            let fics = tagsToWorks[tag]!
            let uniqFicCount = fics.count
            let ficCount = fics.map(\.viewCount).sum
            let uniqWordCount = fics.map(\.wordCount).sum
            let wordCount = fics.map { $0.wordCount * $0.viewCount }.sum
            return "\(tag): \(uniqFicCount) fics (read \(ficCount) times), totalling \(uniqWordCount) words (\(wordCount) words read)"
        }
        func topTagsByProperty(mapper: ([Work]) -> Int, title: String) {
            print("Top tags (\(title)):")
            let tagsByProperty = tagsToWorks.mapValues(mapper).sorted{ $0.value > $1.value }
            let topTagsByProperty = tagsByProperty.prefix(5).map { tag, prop -> String in tag }
            let topTagsByPropertyStrings = topTagsByProperty.map(generateStringForTag)
            print(topTagsByPropertyStrings.joined(separator: "\n"))
        }

        topTagsByProperty(mapper: \.count, title: "unique fics")
        print("---")
        topTagsByProperty(mapper: { $0.map(\.viewCount).sum }, title: "total reads")
        print("---")
        topTagsByProperty(mapper: { $0.map(\.wordCount).sum }, title: "unique words read")
        print("---")
        topTagsByProperty(mapper: { $0.map { $0.wordCount * $0.viewCount }.sum }, title: "total words read")

        print("===")
        if let author = author, let works = authorsToWorks[author] {
            guard let longestWork = works.max(by: { $0.wordCount < $1.wordCount }) else {
                fatalError()
            }
            guard let mostReadFic = works.max(by: { $0.viewCount < $1.viewCount }) else {
                fatalError()
            }
            let uniqueFicCount = works.count
            let ficCount = works.map(\.viewCount).sum
            let uniqueWordCount = works.map(\.wordCount).sum
            let wordCount = works.map { $0.wordCount * $0.viewCount }.sum
            print("""
                  AUTHOR: \(author)
                  uniq_fic_count: \(uniqueFicCount)
                  fic_count: \(ficCount)
                  uniq_word_count: \(uniqueWordCount)
                  word_count: \(wordCount)
                  most_read_fic: "\(mostReadFic.title)" by \(mostReadFic.authors.joined(separator: ", ")) (\(mostReadFic.viewCount)x)
                  longest_fic: "\(longestWork.title)" by \(longestWork.authors.joined(separator: ", ")) (\(longestWork.wordCount) words)
                  """)
            let mostProlificFandom = fandomsToWorks.mapValues { $0.filter { $0.authors.contains(author) }.count }.max { $0.value < $1.value }!
            print("Most prolific fandom: \(mostProlificFandom.key) (\(mostProlificFandom.value) works)")
        }

        print("===")
        if let fandom = fandom, let works = fandomsToWorks[fandom] {
            guard let longestWork = works.max(by: { $0.wordCount < $1.wordCount }) else {
                fatalError()
            }
            guard let mostReadFic = works.max(by: { $0.viewCount < $1.viewCount }) else {
                fatalError()
            }
            let uniqueFicCount = works.count
            let ficCount = works.map(\.viewCount).sum
            let uniqueWordCount = works.map(\.wordCount).sum
            let wordCount = works.map { $0.wordCount * $0.viewCount }.sum
            print("""
                  FANDOM: \(fandom)
                  uniq_fic_count: \(uniqueFicCount)
                  fic_count: \(ficCount)
                  uniq_word_count: \(uniqueWordCount)
                  word_count: \(wordCount)
                  most_read_fic: "\(mostReadFic.title)" by \(mostReadFic.authors.joined(separator: ", ")) (\(mostReadFic.viewCount)x)
                  longest_fic: "\(longestWork.title)" by \(longestWork.authors.joined(separator: ", ")) (\(longestWork.wordCount) words)
                  """)
            let mostProlificAuthor = authorsToWorks.mapValues { $0.filter { $0.fandoms.contains(fandom) }.count }.max { $0.value < $1.value }!
            print("Most prolific author: \(mostProlificAuthor.key) (\(mostProlificAuthor.value) works)")
        }

        print("===")
        if let work = work {
            guard let w = allWorks.first(where: { $0.title == work }) else {
                print("Cannot find work '\(work)'")
                return
            }
            dump(w)
        }
    }
}

extension Collection where Element == Int {
    public var sum: Int {
        self.reduce(0, +)
    }
}
