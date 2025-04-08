from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import random

class MyIntents:
    def __init__(self, responses):
        self.responses = responses

    def get_intents(self):
        # TF-IDF Vectorization
        self.vectorizer = TfidfVectorizer()
        X = self.vectorizer.fit_transform(self.responses)

        # Mini-Batch K-Means Clustering
        n_clusters = 200
        self.model = KMeans(n_clusters=n_clusters, n_init=20, max_iter=1000, random_state=42)
        self.model.fit(X)

        # Create clusters dictionary
        self.clusters = {}
        for i, label in enumerate(self.model.labels_):
            if label not in self.clusters:
                self.clusters[label] = []
            self.clusters[label].append(self.responses[i])

    def get_response(self, message):
        user_msg = message.content
        user_vector = self.vectorizer.transform([user_msg])
        label = self.model.predict(user_vector)[0]
        closest_responses = self.clusters[label]

        weights = [i*i for i in range(len(closest_responses), 0, -1)]
        selected_response = random.choices(closest_responses, weights=weights)
        if not selected_response[0] or len(selected_response[0]) == 0 or selected_response[0].isspace():
            return self.get_response(message)
        return selected_response[0]