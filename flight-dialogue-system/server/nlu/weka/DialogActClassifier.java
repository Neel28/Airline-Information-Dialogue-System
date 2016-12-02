// DialogActClassifier.java
// arguments: <model file path> <utterance file path>

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.ObjectInputStream;
import java.io.FileInputStream;
import weka.core.Instances;
import weka.core.Instance;
import weka.classifiers.trees.J48;
import weka.classifiers.Classifier;
import weka.core.SerializationHelper;
import weka.classifiers.meta.FilteredClassifier;

class DialogActClassifier {
    public static void main(String[] args) {
        try {
            FilteredClassifier tree = (FilteredClassifier) SerializationHelper.read(args[0]);
            Instances unlabeled = new Instances(new BufferedReader(new FileReader(args[1])));
            unlabeled.setClassIndex(unlabeled.numAttributes() - 1);
            Instances labeled = new Instances(unlabeled);
            for (int i = 0; i < unlabeled.numInstances(); i++) {
                double clsLabel = tree.classifyInstance(unlabeled.instance(i));
                labeled.instance(i).setClassValue(clsLabel);
            }
            Instance firstInstance = labeled.firstInstance();
            System.out.println(firstInstance.stringValue(firstInstance.classIndex()));
        }
        catch (Exception e) {
            e.printStackTrace();
        }
    }
}