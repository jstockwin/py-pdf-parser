#!groovy
// These 2 need to be authorized using jenkins script approval
// http://your.jenkins.host/scriptApproval/
import groovy.json.JsonOutput
import java.util.Optional

// Add whichever params you think you'd most want to have
// replace the slackURL below with the hook url provided by
// slack when you configure the webhook

def notifySlack(text, channel, attachments) {
    //your  slack integration url
    def slackURL = 'https://hooks.slack.com/services/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'
    def payload = JsonOutput.toJson([text      : text,
                                     channel   : channel,
                                     username  : "jenkins",
                                     attachments: attachments])

    sh "curl -X POST --data-urlencode \'payload=${payload}\' ${slackURL}"
}

node('docker') {
try {
    // Checkout code from repository
    stage('Checkout') {
        checkout scm
    }

    // Pull the image
    stage('Pull Image') {
        sh 'jenkins_scripts/stages/pull_image.sh'
    }

    // Run linters
    stage('Lint') {
        sh 'jenkins_scripts/stages/lint.sh'
    }

    // Cleanup old docker images
    stage('Cleanup slave node') {
        sh 'jenkins_scripts/stages/cleanup.sh'
    }

    // Notify slack
    stage('Notify Slack') {
        def buildColor = currentBuild.result == null? "good": "warning"
        def buildStatus = currentBuild.result == null? "Success": currentBuild.result
        def buildEmoji = currentBuild.result == null? ":smirk:":":cold_sweat:"

        notifySlack("${buildStatus}", "#bots",
            [[
                title: "${env.JOB_NAME} build ${env.BUILD_NUMBER}",
                color: buildColor,
                text: """${buildEmoji} Build ${buildStatus}.
                |${env.BUILD_URL}
                |branch: ${env.BRANCH_NAME}""".stripMargin()
            ]])
    }

} catch (e) {
    //modify #build-channel to the build channel you want
    //for public channels don't forget the # (hash)
    stage('Notify Slack') {
        notifySlack("build failed", "#bots",
            [[
                title: "${env.JOB_NAME} build ${env.BUILD_NUMBER}",
                color: "danger",
                text: """:dizzy_face: Build finished with error.
                |${env.BUILD_URL}
                |branch: ${env.BRANCH_NAME}""".stripMargin()
            ]])
        throw e
        }
    }
}

node('master') {
    stage('Cleanup repository from master node') {
      // Due to the MultiPipeLine problem with fetching full repository on the
      // master node we need to manually cleanup the workspace to prevent trashing
      // HDD with copies of the git repository
      def workspace = pwd()
      dir("${workspace}@script") {
        deleteDir()
      }
    }
}
